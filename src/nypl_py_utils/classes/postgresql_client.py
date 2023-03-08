import psycopg

from nypl_py_utils.functions.log_helper import create_log
from psycopg.rows import tuple_row
from psycopg_pool import ConnectionPool


class PostgreSQLClient:
    """
    Client for managing connections to a PostgreSQL database (such as Sierra)
    """

    def __init__(self, host, port, db_name, user, password, **kwargs):
        self.logger = create_log('postgresql_client')
        self.db_name = db_name
        self.timeout = kwargs.get('timeout', 300)

        self.conn_info = ('postgresql://{user}:{password}@{host}:{port}/'
                          '{db_name}').format(user=user, password=password,
                                              host=host, port=port,
                                              db_name=db_name)
        self.kwargs = kwargs
        self.kwargs['min_size'] = kwargs.get('min_size', 0)
        self.kwargs['max_size'] = kwargs.get('max_size', 1)
        self.pool = ConnectionPool(self.conn_info, open=False, **self.kwargs)

    def connect(self):
        """
        Opens the connection pool and connects to the given PostgreSQL database
        min_size number of times.
        """
        self.logger.info('Connecting to {} database'.format(self.db_name))
        try:
            if self.pool is None:
                self.pool = ConnectionPool(
                    self.conn_info, open=False, **self.kwargs)
            self.pool.open(wait=True, timeout=self.timeout)
        except psycopg.Error as e:
            self.logger.error(
                'Error connecting to {name} database: {error}'.format(
                    name=self.db_name, error=e))
            raise PostgreSQLClientError(
                'Error connecting to {name} database: {error}'.format(
                    name=self.db_name, error=e)) from None

    def execute_query(self, query, is_write_query=False, query_params=None,
                      row_factory=tuple_row):
        """
        Requests a connection from the pool and uses it to execute an arbitrary
        query. After the query is complete, returns the connection to the pool.

        Parameters
        ----------
        query: str
            The query to execute
        is_write_query: bool, optional
            Whether or not the query is writing to the database, in which case
            the transaction needs to be committed and None should be returned
        query_params: sequence, optional
            The values to be used in a parameterized query
        row_factory: RowFactory, optional
            A psycopg RowFactory that determines how the data will be returned.
            Defaults to tuple_row, which returns the rows as a list of tuples.

        Returns
        -------
        None or sequence
            None if is_write_query is True. Some type of sequence based on
            the row_factory input if is_write_query is False.
        """
        self.logger.info('Querying {} database'.format(self.db_name))
        self.logger.debug('Executing query {}'.format(query))
        with self.pool.connection() as conn:
            try:
                conn.row_factory = row_factory
                cursor = conn.execute(query, query_params)
                if is_write_query:
                    conn.commit()
                    return None
                else:
                    return cursor.fetchall()
            except Exception as e:
                conn.rollback()
                self.logger.error(
                    ('Error executing {name} database query \'{query}\': '
                     '{error}').format(
                        name=self.db_name, query=query, error=e))
                raise PostgreSQLClientError(
                    ('Error executing {name} database query \'{query}\': '
                     '{error}').format(
                        name=self.db_name, query=query, error=e)) from None

    def close_connection(self):
        """Closes the connection pool"""
        self.logger.debug('Closing {} database connection'.format(
            self.db_name))
        self.pool.close()
        self.pool = None


class PostgreSQLClientError(Exception):
    def __init__(self, message=None):
        self.message = message
