import mssql_python
import pandas as pd
import pytest

from nypl_py_utils.classes.azure_client import AzureClient, AzureClientError
from pandas.testing import assert_frame_equal


class TestAzureClient:
    @pytest.fixture
    def mock_azure_conn(self, mocker):
        return mocker.patch("nypl_py_utils.classes.azure_client.mssql_python.connect")

    @pytest.fixture
    def test_instance(self):
        return AzureClient(
            server="test_server",
            database="test_database",
            user="test_user",
            password="test_password",
        )

    def test_connect_success(self, mock_azure_conn, test_instance):
        test_instance.connect()

        assert test_instance.conn == mock_azure_conn.return_value
        mock_azure_conn.return_value.setencoding.assert_called_once_with(
            encoding="utf-8"
        )
        mock_azure_conn.return_value.setdecoding.assert_called_once_with(
            sqltype=mssql_python.SQL_WCHAR, encoding="utf-8"
        )
        # credentials are interpolated into connection string
        connection_str = mock_azure_conn.call_args.kwargs["connection_str"]
        assert connection_str == (
            "Server=test_server;Database=test_database;"
            "UID=test_user;PWD=test_password;Encrypt=yes;"
        )

    def test_connect_retry_success(self, mock_azure_conn, test_instance, mocker):
        mock_sleep = mocker.patch("nypl_py_utils.classes.azure_client.time.sleep")
        success_conn = mocker.MagicMock()
        mock_azure_conn.side_effect = [
            mssql_python.OperationalError("busy", "ddbc busy"),
            success_conn,
        ]

        test_instance.connect(retry_count=2, backoff_factor=2)

        assert test_instance.conn == success_conn
        assert mock_azure_conn.call_count == 2
        mock_sleep.assert_called_once_with(2**0)

    def test_connect_retry_fail(self, mock_azure_conn, test_instance, mocker, caplog):
        mocker.patch("nypl_py_utils.classes.azure_client.time.sleep")
        mock_azure_conn.side_effect = mssql_python.OperationalError(
            "still busy", "ddbc busy"
        )

        with pytest.raises(AzureClientError):
            test_instance.connect(retry_count=2, backoff_factor=2)

        # retry_count=2 -> three attempts total before giving up
        assert mock_azure_conn.call_count == 3
        assert "Error connecting to test_database database" in caplog.text

    def test_connect_unexpected_error(self, mock_azure_conn, test_instance, caplog):
        mock_azure_conn.side_effect = ValueError("uh oh")

        with pytest.raises(AzureClientError):
            test_instance.connect(retry_count=3)

        assert mock_azure_conn.call_count == 1
        assert "Error connecting to test_database database: uh oh" in caplog.text

    def test_execute_query_no_params_success(
        self, mock_azure_conn, test_instance, mocker
    ):
        test_instance.connect()
        mock_cursor = mocker.MagicMock()
        mock_cursor.fetchall.return_value = [(1, 2), (3, 4)]
        test_instance.conn.cursor.return_value = mock_cursor

        result = test_instance.execute_query("SELECT * FROM t")

        assert result == [(1, 2), (3, 4)]
        mock_cursor.execute.assert_called_once_with("SELECT * FROM t")
        mock_cursor.close.assert_called_once()
    
    def test_execute_query_with_params_success(self, mock_azure_conn, test_instance, mocker):
        test_instance.connect()
        mock_cursor = mocker.MagicMock()
        mock_cursor.fetchall.return_value = []
        test_instance.conn.cursor.return_value = mock_cursor

        test_instance.execute_query("SELECT ?", params=("a",))

        mock_cursor.execute.assert_called_once_with("SELECT ?", ("a",))

    def test_execute_query_no_params_returns_dataframe_success(
        self, mock_azure_conn, test_instance, mocker
    ):
        test_instance.connect()
        mock_cursor = mocker.MagicMock()
        mock_cursor.description = [("col1",), ("col2",)]
        mock_cursor.fetchall.return_value = [(1, 2), (3, 4)]
        test_instance.conn.cursor.return_value = mock_cursor

        result = test_instance.execute_query("SELECT * FROM t", dataframe=True)

        expected = pd.DataFrame({"col1": [1, 3], "col2": [2, 4]})
        assert_frame_equal(result, expected)

    def test_execute_query_with_params_returns_dataframe_success(
        self, mock_azure_conn, test_instance, mocker
    ):  
        test_instance.connect()
        mock_cursor = mocker.MagicMock()
        mock_cursor.description = [("col1",), ("col2",)]
        mock_cursor.fetchall.return_value = [(1, 2), (3, 4)]
        test_instance.conn.cursor.return_value = mock_cursor
        expected = pd.DataFrame({"col1": [1, 3], "col2": [2, 4]})
        
        result = test_instance.execute_query(
            "SELECT * FROM t WHERE col1 = ?", params=("a",), dataframe=True
        )

        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM t WHERE col1 = ?", ("a",)
        )
        assert_frame_equal(result, expected)

    def test_execute_query_fail(
        self, mock_azure_conn, test_instance, mocker, caplog
    ):
        test_instance.connect()
        mock_conn = test_instance.conn
        mock_cursor = mocker.MagicMock()
        mock_cursor.execute.side_effect = Exception("bad query")
        mock_conn.cursor.return_value = mock_cursor

        with pytest.raises(AzureClientError):
            test_instance.execute_query("SELECT bad")

        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()
        assert test_instance.conn is None
        mock_cursor.close.assert_called_once()
        assert "Error executing test_database query 'SELECT bad'" in caplog.text
    
    def test_execute_query_without_connection(self, test_instance, caplog):
        assert test_instance.conn is None

        with pytest.raises(AzureClientError):
            test_instance.execute_query("SELECT 1")

        assert "No active database connection" in caplog.text

    def test_close_connection_success(self, mock_azure_conn, test_instance):
        test_instance.connect()
        mock_conn = test_instance.conn

        test_instance.close_connection()

        mock_conn.close.assert_called_once()
        assert test_instance.conn is None

    def test_close_connection_when_already_closed(self, test_instance):
        # no connection -> nothing to close, so nothing happens & no error
        assert test_instance.conn is None
        test_instance.close_connection()
        assert test_instance.conn is None