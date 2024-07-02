import mysql.connector

from nypl_py_utils.functions.log_helper import create_log


class MySQLClient:
    """Client for managing connections to a MySQL database"""

    def __init__(self, host, port, database, user, password):
        self.logger = create_log('mysql_client')
        self.conn = None
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password

    def connect(self, **kwargs):
        """
        Connects to a MySQL database using the given credentials.

        Keyword args can be passed into the connection to set certain options.
        All possible arguments can be found here:
        https://dev.mysql.com/doc/connector-python/en/connector-python-connectargs.html.

        Common arguments include:
            autocommit: bool
                Whether to automatically commit each query rather than running
                them as part of a transaction. By default False.
        """
        self.logger.info('Connecting to {} database'.format(self.database))
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                **kwargs)
        except mysql.connector.Error as e:
            self.logger.error(
                'Error connecting to {name} database: {error}'.format(
                    name=self.database, error=e))
            raise MySQLClientError(
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
            The values to be used in a parameterized query
        kwargs:
            All possible arguments can be found here:
            https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlconnection-cursor.html.

            Common arguments include:
                dictionary: bool
                    Whether the data will be returned as a dictionary. Defaults
                    to False, meaning the data is returned as a list of tuples.

        Returns
        -------
        None or sequence
            None if the cursor has nothing to return. A list of either tuples
            or dictionaries (based on the dictionary input) if there's
            something to return (even if the result set is empty).
        """
        self.logger.info('Querying {} database'.format(self.database))
        self.logger.debug('Executing query {}'.format(query))
        try:
            cursor = self.conn.cursor(**kwargs)
            cursor.execute(query, query_params)
            if cursor.description is None:
                self.conn.commit()
                return None
            else:
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            self.logger.error(
                ('Error executing {name} database query \'{query}\': {error}')
                .format(name=self.database, query=query, error=e))
            raise MySQLClientError(
                ('Error executing {name} database query \'{query}\': {error}')
                .format(name=self.database, query=query, error=e)) from None
        finally:
            cursor.close()

    def close_connection(self):
        """Closes the database connection"""
        self.logger.debug('Closing {} database connection'.format(
            self.database))
        self.conn.close()


class MySQLClientError(Exception):
    def __init__(self, message=None):
        self.message = message
