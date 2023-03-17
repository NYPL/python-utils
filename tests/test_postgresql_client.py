import pytest

from nypl_py_utils import PostgreSQLClient, PostgreSQLClientError
from psycopg import Error


class TestPostgreSQLClient:

    @pytest.fixture
    def test_instance(self, mocker):
        mocker.patch('psycopg_pool.ConnectionPool.open')
        mocker.patch('psycopg_pool.ConnectionPool.close')
        return PostgreSQLClient('test_host', 'test_port', 'test_db_name',
                                'test_user', 'test_password')

    def test_init(self, test_instance):
        assert test_instance.pool.conninfo == (
            'postgresql://test_user:test_password@test_host:test_port/' +
            'test_db_name')
        assert test_instance.pool._opened is False
        assert test_instance.pool.min_size == 0
        assert test_instance.pool.max_size == 1

    def test_init_with_kwargs(self):
        test_instance = PostgreSQLClient(
            'test_host', 'test_port', 'test_db_name', 'test_user',
            'test_password', min_size=5, max_size=10, max_idle=15.0)
        assert test_instance.pool.conninfo == (
            'postgresql://test_user:test_password@test_host:test_port/' +
            'test_db_name')
        assert test_instance.pool._opened is False
        assert test_instance.pool.min_size == 5
        assert test_instance.pool.max_size == 10
        assert test_instance.pool.max_idle == 15.0

    def test_connect(self, test_instance):
        test_instance.connect()
        test_instance.pool.open.assert_called_once_with(wait=True, timeout=300)

    def test_connect_with_exception(self, mocker):
        mocker.patch('psycopg_pool.ConnectionPool.open',
                     side_effect=Error())

        test_instance = PostgreSQLClient(
            'test_host', 'test_port', 'test_db_name', 'test_user',
            'test_password', timeout=1.0)

        with pytest.raises(PostgreSQLClientError):
            test_instance.connect()

    def test_execute_read_query(self, test_instance, mocker):
        test_instance.connect()

        mock_cursor = mocker.MagicMock()
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

        mock_conn = mocker.MagicMock()
        mock_conn_context = mocker.MagicMock()
        mock_conn_context.__enter__.return_value = mock_conn
        mocker.patch('psycopg_pool.ConnectionPool.connection',
                     return_value=mock_conn_context)

        assert test_instance.execute_query(
            'test query', is_write_query=True) is None
        mock_conn.execute.assert_called_once_with('test query', None)
        mock_conn.commit.assert_called_once()

    def test_execute_write_query_with_params(self, test_instance, mocker):
        test_instance.connect()

        mock_conn = mocker.MagicMock()
        mock_conn_context = mocker.MagicMock()
        mock_conn_context.__enter__.return_value = mock_conn
        mocker.patch('psycopg_pool.ConnectionPool.connection',
                     return_value=mock_conn_context)

        assert test_instance.execute_query(
            'test query %s %s', is_write_query=True,
            query_params=('a', 1)) is None
        mock_conn.execute.assert_called_once_with('test query %s %s',
                                                  ('a', 1))
        mock_conn.commit.assert_called_once()

    def test_execute_query_with_exception(self, test_instance, mocker):
        test_instance.connect()

        mock_conn = mocker.MagicMock()
        mock_conn.execute.side_effect = Exception()
        mock_conn_context = mocker.MagicMock()
        mock_conn_context.__enter__.return_value = mock_conn
        mocker.patch('psycopg_pool.ConnectionPool.connection',
                     return_value=mock_conn_context)

        with pytest.raises(PostgreSQLClientError):
            test_instance.execute_query('test query')

        mock_conn.rollback.assert_called_once()

    def test_close_connection(self, test_instance):
        test_instance.connect()
        test_instance.close_connection()
        assert test_instance.pool is None

    def test_reopen_connection(self, test_instance, mocker):
        test_instance.connect()
        test_instance.close_connection()
        test_instance.connect()
        test_instance.pool.open.assert_has_calls([
            mocker.call(wait=True, timeout=300),
            mocker.call(wait=True, timeout=300)])
