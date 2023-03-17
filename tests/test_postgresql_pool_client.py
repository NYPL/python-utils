import pytest

from nypl_py_utils.classes.postgresql_pool_client import (
    PostgreSQLPoolClient, PostgreSQLPoolClientError)
from psycopg import Error


class TestPostgreSQLPoolClient:

    @pytest.fixture
    def test_instance(self, mocker):
        mocker.patch('psycopg_pool.ConnectionPool.open')
        mocker.patch('psycopg_pool.ConnectionPool.close')
        return PostgreSQLPoolClient('test_host', 'test_port', 'test_db_name',
                                    'test_user', 'test_password')

    def test_init(self, test_instance):
        assert test_instance.pool.conninfo == (
            'postgresql://test_user:test_password@test_host:test_port/' +
            'test_db_name')
        assert test_instance.pool._opened is False
        assert test_instance.pool.min_size == 0
        assert test_instance.pool.max_size == 1

    def test_init_with_long_max_idle(self):
        with pytest.raises(PostgreSQLPoolClientError):
            PostgreSQLPoolClient(
                'test_host', 'test_port', 'test_db_name', 'test_user',
                'test_password', max_idle=300.0)

    def test_connect(self, test_instance):
        test_instance.connect()
        test_instance.pool.open.assert_called_once_with(wait=True,
                                                        timeout=300.0)

    def test_connect_with_exception(self, mocker):
        mocker.patch('psycopg_pool.ConnectionPool.open',
                     side_effect=Error())

        test_instance = PostgreSQLPoolClient(
            'test_host', 'test_port', 'test_db_name', 'test_user',
            'test_password')

        with pytest.raises(PostgreSQLPoolClientError):
            test_instance.connect(timeout=1.0)

    def test_execute_read_query(self, test_instance, mocker):
        test_instance.connect()

        mock_cursor = mocker.MagicMock()
        mock_cursor.description = [('description', None, None)]
        mock_cursor.fetchall.return_value = [(1, 2, 3), ('a', 'b', 'c')]
        mock_conn = mocker.MagicMock()
        mock_conn.execute.return_value = mock_cursor
        mock_conn_context = mocker.MagicMock()
        mock_conn_context.__enter__.return_value = mock_conn
        mocker.patch('psycopg_pool.ConnectionPool.connection',
                     return_value=mock_conn_context)

        assert test_instance.execute_query(
            'test query') == [(1, 2, 3), ('a', 'b', 'c')]
        mock_conn.execute.assert_called_once_with('test query', None)
        mock_cursor.fetchall.assert_called_once()

    def test_execute_write_query(self, test_instance, mocker):
        test_instance.connect()

        mock_cursor = mocker.MagicMock()
        mock_cursor.description = None
        mock_conn = mocker.MagicMock()
        mock_conn.execute.return_value = mock_cursor
        mock_conn_context = mocker.MagicMock()
        mock_conn_context.__enter__.return_value = mock_conn
        mocker.patch('psycopg_pool.ConnectionPool.connection',
                     return_value=mock_conn_context)

        assert test_instance.execute_query('test query') is None
        mock_conn.execute.assert_called_once_with('test query', None)

    def test_execute_write_query_with_params(self, test_instance, mocker):
        test_instance.connect()

        mock_cursor = mocker.MagicMock()
        mock_cursor.description = None
        mock_conn = mocker.MagicMock()
        mock_conn.execute.return_value = mock_cursor
        mock_conn_context = mocker.MagicMock()
        mock_conn_context.__enter__.return_value = mock_conn
        mocker.patch('psycopg_pool.ConnectionPool.connection',
                     return_value=mock_conn_context)

        assert test_instance.execute_query(
            'test query %s %s', query_params=('a', 1)) is None
        mock_conn.execute.assert_called_once_with('test query %s %s',
                                                  ('a', 1))

    def test_execute_query_with_exception(self, test_instance, mocker):
        test_instance.connect()

        mock_conn = mocker.MagicMock()
        mock_conn.execute.side_effect = Exception()
        mock_conn_context = mocker.MagicMock()
        mock_conn_context.__enter__.return_value = mock_conn
        mocker.patch('psycopg_pool.ConnectionPool.connection',
                     return_value=mock_conn_context)

        with pytest.raises(PostgreSQLPoolClientError):
            test_instance.execute_query('test query')

    def test_close_pool(self, test_instance):
        test_instance.connect()
        test_instance.close_pool()
        assert test_instance.pool is None

    def test_reopen_pool(self, test_instance, mocker):
        test_instance.connect()
        test_instance.close_pool()
        test_instance.connect()
        test_instance.pool.open.assert_has_calls([
            mocker.call(wait=True, timeout=300),
            mocker.call(wait=True, timeout=300)])
