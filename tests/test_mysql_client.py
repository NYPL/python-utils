import pytest

from nypl_py_utils import MySQLClient, MySQLClientError


class TestMySQLClient:

    @pytest.fixture
    def mock_mysql_conn(self, mocker):
        return mocker.patch('mysql.connector.connect')

    @pytest.fixture
    def test_instance(self):
        return MySQLClient('test_host', 'test_port', 'test_database',
                           'test_user', 'test_password')

    def test_connect(self, mock_mysql_conn, test_instance):
        test_instance.connect()
        mock_mysql_conn.assert_called_once_with(host='test_host',
                                                port='test_port',
                                                database='test_database',
                                                user='test_user',
                                                password='test_password')

    def test_execute_read_query(self, mock_mysql_conn, test_instance, mocker):
        test_instance.connect()

        mock_cursor = mocker.MagicMock()
        mock_cursor.fetchall.return_value = [(1, 2, 3), ('a', 'b', 'c')]
        test_instance.conn.cursor.return_value = mock_cursor

        assert test_instance.execute_query(
            'test query') == [(1, 2, 3), ('a', 'b', 'c')]
        test_instance.conn.cursor.called_once_with(dictionary=False)
        mock_cursor.execute.assert_called_once_with('test query', None)
        mock_cursor.close.assert_called_once()

    def test_execute_dictionary_read_query(self, mock_mysql_conn,
                                           test_instance, mocker):
        test_instance.connect()

        mock_cursor = mocker.MagicMock()
        mock_cursor.fetchall.return_value = [
            {'col1': 1, 'col2': 'a'},
            {'col1': 2, 'col2': 'b'},
            {'col1': 3, 'col2': 'c'}]
        test_instance.conn.cursor.return_value = mock_cursor

        assert test_instance.execute_query(
            'test query', dictionary=True) == [{'col1': 1, 'col2': 'a'},
                                               {'col1': 2, 'col2': 'b'},
                                               {'col1': 3, 'col2': 'c'}]
        test_instance.conn.cursor.called_once_with(dictionary=True)
        mock_cursor.execute.assert_called_once_with('test query', None)
        mock_cursor.close.assert_called_once()

    def test_execute_write_query(self, mock_mysql_conn, test_instance, mocker):
        test_instance.connect()

        mock_cursor = mocker.MagicMock()
        test_instance.conn.cursor.return_value = mock_cursor

        assert test_instance.execute_query(
            'test query', is_write_query=True) is None
        test_instance.conn.cursor.called_once_with(dictionary=False)
        mock_cursor.execute.assert_called_once_with('test query', None)
        test_instance.conn.commit.called_once()
        mock_cursor.close.assert_called_once()

    def test_execute_write_query_with_params(self, mock_mysql_conn,
                                             test_instance, mocker):
        test_instance.connect()

        mock_cursor = mocker.MagicMock()
        test_instance.conn.cursor.return_value = mock_cursor

        assert test_instance.execute_query(
            'test query %s %s', is_write_query=True,
            query_params=('a', 1)) is None
        test_instance.conn.cursor.called_once_with(dictionary=False)
        mock_cursor.execute.assert_called_once_with('test query %s %s',
                                                    ('a', 1))
        test_instance.conn.commit.called_once()
        mock_cursor.close.assert_called_once()

    def test_execute_query_with_exception(
            self, mock_mysql_conn, test_instance, mocker):
        test_instance.connect()

        mock_cursor = mocker.MagicMock()
        mock_cursor.execute.side_effect = Exception()
        test_instance.conn.cursor.return_value = mock_cursor

        with pytest.raises(MySQLClientError):
            test_instance.execute_query('test query')

        test_instance.conn.rollback.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_close_connection(self, mock_mysql_conn, test_instance):
        test_instance.connect()
        test_instance.close_connection()
        test_instance.conn.close.assert_called_once()
