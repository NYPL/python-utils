import psycopg

from nypl_py_utils.functions.log_helper import create_log
from psycopg_pool import ConnectionPool


class PostgreSQLClient:
    """
    Client for managing connections to a PostgreSQL database (such as Sierra)
    """

    def __init__(self, host, port, db_name, user, password, **kwargs):
        self.logger = create_log('postgresql_client')
        self.db_name = db_name
        self.timeout = kwargs.get('timeout', 300)

        conn_info = 'postgresql://{user}:{password}@{host}:{port}/{db_name}'\
            .format(user=user, password=password, host=host, port=port,
                    db_name=db_name)
        self.pool = ConnectionPool(
            conn_info, open=False,
            min_size=kwargs.get('min_size', 1),
            max_size=kwargs.get('max_size', None))

    def connect(self):
        """
        Opens the connection pool and connects to the given PostgreSQL database
        min_size number of times.
        """
        self.logger.info('Connecting to {} database'.format(self.db_name))
        try:
            self.pool.open(wait=True, timeout=self.timeout)
        except psycopg.Error as e:
            self.logger.error(
                'Error connecting to {name} database: {error}'.format(
                    name=self.db_name, error=e))
            raise PostgreSQLClientError(
                'Error connecting to {name} database: {error}'.format(
                    name=self.db_name, error=e)) from None

    def execute_query(self, query):
        """
        Requests a connection from the pool and uses it to execute an arbitrary
        query. After the query is complete, returns the connection to the pool.

        Returns a sequence of tuples representing the rows returned by the
        query.
        """
        self.logger.info('Querying {} database'.format(self.db_name))
        self.logger.debug('Executing query {}'.format(query))
        with self.pool.connection() as conn:
            try:
                return conn.execute(query).fetchall()
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


class PostgreSQLClientError(Exception):
    def __init__(self, message=None):
        self.message = message
