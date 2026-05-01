import pytest

from nypl_py_utils.classes.snowflake_client import (
    SnowflakeClient, SnowflakeClientError
)


class TestSnowflakeClient:

    @pytest.fixture
    def mock_snowflake_conn(self, mocker):
        return mocker.patch('snowflake.connector.connect')

    @pytest.fixture
    def test_instance(self):
        return SnowflakeClient(
            {'account': 'test_account', 'user': 'test_user'}
        )

    def test_connect(self, mock_snowflake_conn, test_instance):
        test_instance.connect()
        mock_snowflake_conn.assert_called_once_with(
            account='test_account', user='test_user')

    def test_execute_query(
            self, mock_snowflake_conn, test_instance, mocker):
        test_instance.connect()

        mock_cursor = mocker.MagicMock()
        mock_cursor.fetchall.return_value = [(1, 2, 3), ('a', 'b', 'c')]
        test_instance.conn.cursor.return_value = mock_cursor

        assert test_instance.execute_query(
            'test query') == [(1, 2, 3), ('a', 'b', 'c')]
        mock_cursor.execute.assert_called_once_with('test query')
        mock_cursor.close.assert_called_once()

    def test_execute_query_with_exception(
            self, mock_snowflake_conn, test_instance, mocker):
        test_instance.connect()

        mock_cursor = mocker.MagicMock()
        mock_cursor.execute.side_effect = Exception()
        test_instance.conn.cursor.return_value = mock_cursor

        with pytest.raises(SnowflakeClientError):
            test_instance.execute_query('test query')

        mock_cursor.close.assert_called()
        test_instance.conn.close.assert_called_once()

    def test_close_connection(self, mock_snowflake_conn, test_instance):
        test_instance.connect()
        test_instance.close_connection()
        test_instance.conn.close.assert_called_once()
