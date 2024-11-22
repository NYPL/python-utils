import psycopg
import time

from nypl_py_utils.functions.log_helper import create_log


class PostgreSQLClient:
    """Client for managing individual connections to a PostgreSQL database"""

    def __init__(self, host, port, database, user, password):
        self.logger = create_log('postgresql_client')
        self.conn = None
        self.conn_info = ('postgresql://{user}:{password}@{host}:{port}/'
                          '{database}').format(user=user, password=password,
                                               host=host, port=port,
                                               database=database)
        self.database = database

    def connect(self, retry_count=0, backoff_factor=5, **kwargs):
        """
        Connects to a PostgreSQL database using the given credentials.

        Parameters
        ----------
        retry_count: int, optional
            The number of times to retry connecting before throwing an error.
            By default no retry occurs.
        backoff_factor: int, optional
            The backoff factor when retrying. The amount of time to wait before
            retrying is backoff_factor ** number_of_retries_made.
        kwargs:
            All possible arguments (such as the row_factory) can be found here:
            https://www.psycopg.org/psycopg3/docs/api/connections.html#psycopg.Connection.connect
        """
        self.logger.info('Connecting to {} database'.format(self.database))
        attempt_count = 0
        while attempt_count <= retry_count:
            try:
                try:
                    self.conn = psycopg.connect(self.conn_info, **kwargs)
                    break
                except (psycopg.OperationalError,
                        psycopg.errors.ConnectionTimeout):
                    if attempt_count < retry_count:
                        self.logger.info('Failed to connect -- retrying')
                        time.sleep(backoff_factor ** attempt_count)
                        attempt_count += 1
                    else:
                        raise
            except Exception as e:
                self.logger.error(
                    'Error connecting to {name} database: {error}'.format(
                        name=self.database, error=e))
                raise PostgreSQLClientError(
                    'Error connecting to {name} database: {error}'.format(
                        name=self.database, error=e)) from None

    def execute_query(self, query, query_params=None, **kwargs):
        """
        Executes an arbitrary query against the given database connection.

        Parameters
        ----------
        query: str
            The query to execute
        query_params: sequence, optional
            The values to be used in a parameterized query. The values can be
            for a single insert query -- e.g. execute_query(
                "INSERT INTO x VALUES (%s, %s)", (1, "a"))
            or for multiple -- e.g execute_transaction(
                "INSERT INTO x VALUES (%s, %s)", [(1, "a"), (2, "b")])
        kwargs:
            All possible arguments can be found here:
            https://www.psycopg.org/psycopg3/docs/api/cursors.html#psycopg.Cursor.execute

        Returns
        -------
        None or sequence
            None if the cursor has nothing to return. Some type of sequence
            based on the connection's row_factory if there's something to
            return (even if the result set is empty).
        """
        self.logger.info('Querying {} database'.format(self.database))
        self.logger.debug('Executing query {}'.format(query))
        try:
            cursor = self.conn.cursor()
            if query_params is not None and all(
                isinstance(param, tuple) or isinstance(param, list)
                for param in query_params
            ):
                cursor.executemany(query, query_params, **kwargs)
            else:
                cursor.execute(query, query_params, **kwargs)
            self.conn.commit()
            return None if cursor.description is None else cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            cursor.close()
            self.close_connection()
            self.logger.error(
                ('Error executing {name} database query \'{query}\': '
                    '{error}').format(
                    name=self.database, query=query, error=e))
            raise PostgreSQLClientError(
                ('Error executing {name} database query \'{query}\': '
                    '{error}').format(
                    name=self.database, query=query, error=e)) from None
        finally:
            cursor.close()

    def close_connection(self):
        """Closes the database connection"""
        self.logger.debug('Closing {} database connection'.format(
            self.database))
        self.conn.close()


class PostgreSQLClientError(Exception):
    def __init__(self, message=None):
        self.message = message
