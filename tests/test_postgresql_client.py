import pytest

from nypl_py_utils.classes.postgresql_client import (
    PostgreSQLClient, PostgreSQLClientError)


class TestPostgreSQLClient:

    @pytest.fixture
    def mock_pg_conn(self, mocker):
        return mocker.patch('psycopg.connect')

    @pytest.fixture
    def test_instance(self):
        return PostgreSQLClient('test_host', 'test_port', 'test_db_name',
                                'test_user', 'test_password')

    def test_connect(self, mock_pg_conn, test_instance):
        test_instance.connect()
        mock_pg_conn.assert_called_once_with(
            'postgresql://test_user:test_password@test_host:test_port/' +
            'test_db_name')

    def test_execute_read_query(self, mock_pg_conn, test_instance, mocker):
        test_instance.connect()

        mock_cursor = mocker.MagicMock()
        mock_cursor.description = [('description', None, None)]
        mock_cursor.execute.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [(1, 2, 3), ('a', 'b', 'c')]
        test_instance.conn.cursor.return_value = mock_cursor

        assert test_instance.execute_query(
            'test query') == [(1, 2, 3), ('a', 'b', 'c')]
        mock_cursor.execute.assert_called_once_with('test query', None)
        test_instance.conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_execute_write_query(self, mock_pg_conn, test_instance, mocker):
        test_instance.connect()

        mock_cursor = mocker.MagicMock()
        mock_cursor.description = None
        test_instance.conn.cursor.return_value = mock_cursor

        assert test_instance.execute_query('test query') is None
        mock_cursor.execute.assert_called_once_with('test query', None)
        test_instance.conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_execute_write_query_with_params(self, mock_pg_conn, test_instance,
                                             mocker):
        test_instance.connect()

        mock_cursor = mocker.MagicMock()
        mock_cursor.description = None
        test_instance.conn.cursor.return_value = mock_cursor

        assert test_instance.execute_query(
            'test query %s %s', query_params=('a', 1)) is None
        mock_cursor.execute.assert_called_once_with('test query %s %s',
                                                    ('a', 1))
        test_instance.conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_execute_query_with_exception(
            self, mock_pg_conn, test_instance, mocker):
        test_instance.connect()

        mock_cursor = mocker.MagicMock()
        mock_cursor.execute.side_effect = Exception()
        test_instance.conn.cursor.return_value = mock_cursor

        with pytest.raises(PostgreSQLClientError):
            test_instance.execute_query('test query')

        test_instance.conn.rollback.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_close_connection(self, mock_pg_conn, test_instance):
        test_instance.connect()
        test_instance.close_connection()
        test_instance.conn.close.assert_called_once()
