import psycopg

from nypl_py_utils.functions.log_helper import create_log
from psycopg.rows import tuple_row
from psycopg_pool import ConnectionPool


class PostgreSQLPoolClient:
    """Client for managing a connection pool to a PostgreSQL database"""

    def __init__(self, host, port, db_name, user, password, conn_timeout=300.0,
                 **kwargs):
        """
        Creates (but does not open) a connection pool.

        Parameters
        ----------
        host, port, db_name, user, password: str
            Required connection information
        kwargs: dict, optional
            Keyword args to be passed into the ConnectionPool. All possible
            arguments can be found here:
            https://www.psycopg.org/psycopg3/docs/api/pool.html#psycopg_pool.ConnectionPool.

            Common arguments include:
                min_size/max_size: The minimum and maximum size of the pool, by
                    default 0 and 1
                max_idle: Half the number of seconds a connection can stay idle
                    before being automatically closed, by default 90.0, which
                    corresponds to 3 minutes of idle time. Note that if
                    min_size is greater than 0, this won't apply to the first
                    min_size connections, which will stay open until manually
                    closed.
        """
        self.logger = create_log('postgresql_client')
        self.conn_info = ('postgresql://{user}:{password}@{host}:{port}/'
                          '{db_name}').format(user=user, password=password,
                                              host=host, port=port,
                                              db_name=db_name)

        self.db_name = db_name
        self.kwargs = kwargs
        self.kwargs['min_size'] = kwargs.get('min_size', 0)
        self.kwargs['max_size'] = kwargs.get('max_size', 1)
        self.kwargs['max_idle'] = kwargs.get('max_idle', 90.0)

        if self.kwargs['max_idle'] > 150.0:
            self.logger.error((
                'max_idle is too high -- values over 150 seconds are unsafe '
                'and may lead to connection leakages in ECS'))
            raise PostgreSQLPoolClientError((
                'max_idle is too high -- values over 150 seconds are unsafe '
                'and may lead to connection leakages in ECS')) from None

        self.pool = ConnectionPool(self.conn_info, open=False, **self.kwargs)

    def connect(self, timeout=300.0):
        """
        Opens the connection pool and connects to the given PostgreSQL database
        min_size number of times

        Parameters
        ----------
        conn_timeout: float, optional
            The number of seconds to try connecting before throwing an error.
            Defaults to 300 seconds.
        """
        self.logger.info('Connecting to {} database'.format(self.db_name))
        try:
            if self.pool is None:
                self.pool = ConnectionPool(
                    self.conn_info, open=False, **self.kwargs)
            self.pool.open(wait=True, timeout=timeout)
        except psycopg.Error as e:
            self.logger.error(
                'Error connecting to {name} database: {error}'.format(
                    name=self.db_name, error=e))
            raise PostgreSQLPoolClientError(
                'Error connecting to {name} database: {error}'.format(
                    name=self.db_name, error=e)) from None

    def execute_query(self, query, query_params=None, row_factory=tuple_row,
                      **kwargs):
        """
        Requests a connection from the pool and uses it to execute an arbitrary
        query. After the query is complete, either commits it or rolls it back,
        and then returns the connection to the pool.

        Parameters
        ----------
        query: str
            The query to execute
        query_params: sequence, optional
            The values to be used in a parameterized query
        row_factory: RowFactory, optional
            A psycopg RowFactory that determines how the data will be returned.
            Defaults to tuple_row, which returns the rows as a list of tuples.
        kwargs:
            All possible arguments can be found here:
            https://www.psycopg.org/psycopg3/docs/api/cursors.html#psycopg.Cursor.execute

        Returns
        -------
        None or sequence
            None if the cursor has nothing to return. Some type of sequence
            based on the row_factory input if there's something to return
            (even if the result set is empty).
        """
        self.logger.info('Querying {} database'.format(self.db_name))
        self.logger.debug('Executing query {}'.format(query))
        with self.pool.connection() as conn:
            try:
                conn.row_factory = row_factory
                cursor = conn.execute(query, query_params, **kwargs)
                return (None if cursor.description is None
                        else cursor.fetchall())
            except Exception as e:
                self.logger.error(
                    ('Error executing {name} database query \'{query}\': '
                     '{error}').format(
                        name=self.db_name, query=query, error=e))
                raise PostgreSQLPoolClientError(
                    ('Error executing {name} database query \'{query}\': '
                     '{error}').format(
                        name=self.db_name, query=query, error=e)) from None

    def close_pool(self):
        """Closes the connection pool"""
        self.logger.debug('Closing {} database connection pool'.format(
            self.db_name))
        self.pool.close()
        self.pool = None


class PostgreSQLPoolClientError(Exception):
    def __init__(self, message=None):
        self.message = message
