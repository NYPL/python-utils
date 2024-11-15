import pytest

from nypl_py_utils.classes.redshift_client import (
    RedshiftClient, RedshiftClientError)
from redshift_connector import InterfaceError


class TestRedshiftClient:

    @pytest.fixture
    def mock_redshift_conn(self, mocker):
        return mocker.patch('redshift_connector.connect')

    @pytest.fixture
    def test_instance(self):
        return RedshiftClient('test_host', 'test_database', 'test_user',
                              'test_password')

    def test_connect(self, mock_redshift_conn, test_instance):
        test_instance.connect()
        mock_redshift_conn.assert_called_once_with(host='test_host',
                                                   database='test_database',
                                                   user='test_user',
                                                   password='test_password',
                                                   sslmode='verify-full')

    def test_connect_retry_success(self, mock_redshift_conn, test_instance,
                                   mocker):
        mock_redshift_conn.side_effect = [InterfaceError(), mocker.MagicMock()]
        test_instance.connect(retry_count=2, backoff_factor=0)
        assert mock_redshift_conn.call_count == 2

    def test_connect_retry_fail(self, mock_redshift_conn, test_instance):
        mock_redshift_conn.side_effect = InterfaceError()

        with pytest.raises(RedshiftClientError):
            test_instance.connect(retry_count=2, backoff_factor=0)

        assert mock_redshift_conn.call_count == 3

    def test_execute_query(self, mock_redshift_conn, test_instance, mocker):
        test_instance.connect()

        mock_cursor = mocker.MagicMock()
        mock_cursor.fetchall.return_value = [[1, 2, 3], ['a', 'b', 'c']]
        test_instance.conn.cursor.return_value = mock_cursor

        assert test_instance.execute_query(
            'test query') == [[1, 2, 3], ['a', 'b', 'c']]
        mock_cursor.execute.assert_called_once_with('test query')
        mock_cursor.fetchall.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_execute_dataframe_query(self, mock_redshift_conn, test_instance,
                                     mocker):
        test_instance.connect()

        mock_cursor = mocker.MagicMock()
        test_instance.conn.cursor.return_value = mock_cursor

        test_instance.execute_query('test query', dataframe=True)
        mock_cursor.execute.assert_called_once_with('test query')
        mock_cursor.fetch_dataframe.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_execute_query_with_exception(
            self, mock_redshift_conn, test_instance, mocker):
        test_instance.connect()

        mock_cursor = mocker.MagicMock()
        mock_cursor.execute.side_effect = Exception()
        test_instance.conn.cursor.return_value = mock_cursor

        with pytest.raises(RedshiftClientError):
            test_instance.execute_query('test query')

        test_instance.conn.rollback.assert_called_once()
        mock_cursor.close.assert_called()
        test_instance.conn.close.assert_called_once()

    def test_execute_transaction(self, mock_redshift_conn, test_instance,
                                 mocker):
        test_instance.connect()

        mock_cursor = mocker.MagicMock()
        test_instance.conn.cursor.return_value = mock_cursor

        test_instance.execute_transaction([('query 1', None),
                                           ('query 2 %s %s', ('a', 1))])
        mock_cursor.execute.assert_has_calls([
            mocker.call('BEGIN TRANSACTION;'),
            mocker.call('query 1', None),
            mocker.call('query 2 %s %s', ('a', 1)),
            mocker.call('END TRANSACTION;')])
        mock_cursor.executemany.assert_not_called()
        test_instance.conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_execute_transaction_with_many(self, mock_redshift_conn,
                                           test_instance, mocker):
        test_instance.connect()

        mock_cursor = mocker.MagicMock()
        test_instance.conn.cursor.return_value = mock_cursor

        test_instance.execute_transaction([
            ('query 1', None), ('query 2 %s %s', (None, 1)),
            ('query 3 %s %s', [(None, 10), ('b', 20)]), ('query 4', None)])
        mock_cursor.execute.assert_has_calls([
            mocker.call('BEGIN TRANSACTION;'),
            mocker.call('query 1', None),
            mocker.call('query 2 %s %s', (None, 1)),
            mocker.call('query 4', None),
            mocker.call('END TRANSACTION;')])
        mock_cursor.executemany.assert_called_once_with(
            'query 3 %s %s', [(None, 10), ('b', 20)])
        test_instance.conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_execute_transaction_with_exception(
            self, mock_redshift_conn, test_instance, mocker):
        test_instance.connect()

        mock_cursor = mocker.MagicMock()
        mock_cursor.execute.side_effect = [None, None, Exception()]
        test_instance.conn.cursor.return_value = mock_cursor

        with pytest.raises(RedshiftClientError):
            test_instance.execute_transaction(
                [('query 1', None), ('query 2', None)])

        mock_cursor.execute.assert_has_calls([
            mocker.call('BEGIN TRANSACTION;'),
            mocker.call('query 1', None),
            mocker.call('query 2', None)])
        test_instance.conn.commit.assert_not_called()
        test_instance.conn.rollback.assert_called_once()
        mock_cursor.close.assert_called()
        test_instance.conn.close.assert_called_once()

    def test_close_connection(self, mock_redshift_conn, test_instance):
        test_instance.connect()
        test_instance.close_connection()
        test_instance.conn.close.assert_called_once()
