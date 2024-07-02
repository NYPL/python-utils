import psycopg

from nypl_py_utils.functions.log_helper import create_log


class PostgreSQLClient:
    """Client for managing individual connections to a PostgreSQL database"""

    def __init__(self, host, port, db_name, user, password):
        self.logger = create_log('postgresql_client')
        self.conn = None
        self.conn_info = ('postgresql://{user}:{password}@{host}:{port}/'
                          '{db_name}').format(user=user, password=password,
                                              host=host, port=port,
                                              db_name=db_name)

        self.db_name = db_name

    def connect(self, **kwargs):
        """
        Connects to a PostgreSQL database using the given credentials.

        Keyword args can be passed into the connection to set certain options.
        All possible arguments can be found here:
        https://www.psycopg.org/psycopg3/docs/api/connections.html#psycopg.Connection.connect.

        Common arguments include:
            autocommit: bool
                Whether to automatically commit each query rather than running
                them as part of a transaction. By default False.
            row_factory: RowFactory
                A psycopg RowFactory that determines how the data will be
                returned. Defaults to tuple_row, which returns the rows as a
                list of tuples.
        """
        self.logger.info('Connecting to {} database'.format(self.db_name))
        try:
            self.conn = psycopg.connect(self.conn_info, **kwargs)
        except psycopg.Error as e:
            self.logger.error(
                'Error connecting to {name} database: {error}'.format(
                    name=self.db_name, error=e))
            raise PostgreSQLClientError(
                'Error connecting to {name} database: {error}'.format(
                    name=self.db_name, error=e)) from None

    def execute_query(self, query, query_params=None, **kwargs):
        """
        Executes an arbitrary query against the given database connection.

        Parameters
        ----------
        query: str
            The query to execute
        query_params: sequence, optional
            The values to be used in a parameterized query
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
        self.logger.info('Querying {} database'.format(self.db_name))
        self.logger.debug('Executing query {}'.format(query))
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, query_params, **kwargs)
            self.conn.commit()
            return None if cursor.description is None else cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            self.logger.error(
                ('Error executing {name} database query \'{query}\': '
                    '{error}').format(
                    name=self.db_name, query=query, error=e))
            raise PostgreSQLClientError(
                ('Error executing {name} database query \'{query}\': '
                    '{error}').format(
                    name=self.db_name, query=query, error=e)) from None
        finally:
            cursor.close()

    def close_connection(self):
        """Closes the database connection"""
        self.logger.debug('Closing {} database connection'.format(
            self.db_name))
        self.conn.close()


class PostgreSQLClientError(Exception):
    def __init__(self, message=None):
        self.message = message
