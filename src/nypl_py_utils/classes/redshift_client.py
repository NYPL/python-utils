import redshift_connector
import time

from nypl_py_utils.functions.log_helper import create_log


class RedshiftClient:
    """Client for managing connections to Redshift"""

    def __init__(self, host, database, user, password):
        self.logger = create_log('redshift_client')
        self.conn = None
        self.host = host
        self.database = database
        self.user = user
        self.password = password

    def connect(self, retry_count=0, backoff_factor=5):
        """
        Connects to a Redshift database using the given credentials.

        Parameters
        ----------
        retry_count: int, optional
            The number of times to retry connecting before throwing an error.
            By default no retry occurs.
        backoff_factor: int, optional
            The backoff factor when retrying. The amount of time to wait before
            retrying is backoff_factor ** number_of_retries_made.
        """
        self.logger.info('Connecting to {} database'.format(self.database))
        attempt_count = 0
        while attempt_count <= retry_count:
            try:
                try:
                    self.conn = redshift_connector.connect(
                        host=self.host,
                        database=self.database,
                        user=self.user,
                        password=self.password,
                        sslmode='verify-full')
                    break
                except (redshift_connector.InterfaceError):
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
                raise RedshiftClientError(
                    'Error connecting to {name} database: {error}'.format(
                        name=self.database, error=e)) from None

    def execute_query(self, query, dataframe=False):
        """
        Executes an arbitrary read query against the given database connection.

        Parameters
        ----------
        query: str
            The query to execute, assumed to be a read query
        dataframe: bool, optional
            Whether the data will be returned as a pandas DataFrame. Defaults
            to False, which means the data is returned as a list of tuples.

        Returns
        -------
        None or sequence
            A list of tuples or a pandas DataFrame (based on the `dataframe`
            input)
        """
        self.logger.info('Querying {} database'.format(self.database))
        self.logger.debug('Executing query {}'.format(query))
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            if dataframe:
                return cursor.fetch_dataframe()
            else:
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            cursor.close()
            self.close_connection()
            self.logger.error(
                ('Error executing {name} database query \'{query}\': {error}')
                .format(name=self.database, query=query, error=e))
            raise RedshiftClientError(
                ('Error executing {name} database query \'{query}\': {error}')
                .format(name=self.database, query=query, error=e)) from None
        finally:
            cursor.close()

    def execute_transaction(self, queries):
        """
        Executes a series of queries within a single transaction against the
        given database connection. Assumes each of these queries is a write
        query and so does not return anything.

        Parameters
        ----------
        queries: list<tuple>
            A list of tuples containing a query and the values to be used if
            the query is parameterized (or None if it's not). The values can
            be for a single insert query -- e.g. execute_transaction(
                [("INSERT INTO x VALUES (%s, %s)", (1, "a"))])
            or for multiple -- e.g execute_transaction(
                [("INSERT INTO x VALUES (%s, %s)", [(1, "a"), (2, "b")])])
        """
        self.logger.info('Executing transaction against {} database'.format(
            self.database))
        try:
            cursor = self.conn.cursor()
            cursor.execute('BEGIN TRANSACTION;')
            for query in queries:
                self.logger.debug('Executing query {}'.format(query))
                if query[1] is not None and all(
                    isinstance(el, tuple) or isinstance(el, list)
                    for el in query[1]
                ):
                    cursor.executemany(query[0], query[1])
                else:
                    cursor.execute(query[0], query[1])
            cursor.execute('END TRANSACTION;')
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            cursor.close()
            self.close_connection()
            self.logger.error(
                ('Error executing {name} database transaction: {error}')
                .format(name=self.database, error=e))
            raise RedshiftClientError(
                ('Error executing {name} database transaction: {error}')
                .format(name=self.database, error=e)) from None
        finally:
            cursor.close()

    def close_connection(self):
        """Closes the database connection"""
        self.logger.debug('Closing {} database connection'.format(
            self.database))
        self.conn.close()


class RedshiftClientError(Exception):
    def __init__(self, message=None):
        self.message = message
