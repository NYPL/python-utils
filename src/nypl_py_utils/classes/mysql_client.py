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

    def connect(self):
        """Connects to a MySQL database using the given credentials"""
        self.logger.info('Connecting to {} database'.format(self.database))
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password)
        except mysql.connector.Error as e:
            self.logger.error(
                'Error connecting to {name} database: {error}'.format(
                    name=self.database, error=e))
            raise MySQLClientError(
                'Error connecting to {name} database: {error}'.format(
                    name=self.database, error=e)) from None

    def execute_query(self, query):
        """
        Executes an arbitrary query against the given database connection.

        Returns a sequence of tuples representing the rows returned by the
        query.
        """
        self.logger.info('Querying {} database'.format(self.database))
        self.logger.debug('Executing query {}'.format(query))
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
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
