import psycopg2

from nypl_py_utils.functions.log_helper import create_log


class PgClient:
    """
    Client for managing connections to a PostgreSQL database (such as Sierra).
    """

    def __init__(self, host, port, db_name, user, password):
        self.logger = create_log('pg_client')
        self.conn = None
        self.host = host
        self.port = port
        self.db_name = db_name
        self.user = user
        self.password = password

    def connect(self):
        """Connects to a PostgreSQL database using the given credentials"""
        self.logger.info('Connecting to {} database'.format(self.db_name))
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.db_name,
                user=self.user,
                password=self.password)
        except psycopg2.OperationalError as e:
            self.logger.error(
                'Error connecting to {name} database: {error}'.format(
                    name=self.db_name, error=e))
            raise PgClientError(
                'Error connecting to {name} database: {error}'.format(
                    name=self.db_name, error=e)) from None

    def execute_query(self, query):
        """
        Executes an arbitrary query against the given database connection.

        Returns a sequence of tuples representing the rows returned by the
        query.
        """
        self.logger.info('Querying {} database'.format(self.db_name))
        self.logger.debug('Executing query {}'.format(query))
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            self.logger.error(
                ('Error executing {name} database query \'{query}\': {error}')
                .format(name=self.db_name, query=query, error=e))
            raise PgClientError(
                ('Error executing {name} database query \'{query}\': {error}')
                .format(name=self.db_name, query=query, error=e)) from None
        finally:
            cursor.close()

    def close_connection(self):
        """Closes the database connection"""
        self.logger.debug('Closing {} database connection'.format(
            self.db_name))
        self.conn.close()


class PgClientError(Exception):
    def __init__(self, message=None):
        self.message = message
