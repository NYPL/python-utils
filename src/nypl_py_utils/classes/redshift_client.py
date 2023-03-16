import redshift_connector

from botocore.exceptions import ClientError
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

    def connect(self):
        """Connects to a Redshift database using the given credentials"""
        self.logger.info('Connecting to {} database'.format(self.database))
        try:
            self.conn = redshift_connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                sslmode='verify-full')
        except ClientError as e:
            self.logger.error(
                'Error connecting to {name} database: {error}'.format(
                    name=self.database, error=e))
            raise RedshiftClientError(
                'Error connecting to {name} database: {error}'.format(
                    name=self.database, error=e)) from None

    def execute_query(self, query, dataframe=False):
        """
        Executes an arbitrary query against the given database connection.

        Parameters
        ----------
        query: str
            The query to execute
        dataframe: bool, optional
            Whether the data will be returned as a pandas DataFrame. Defaults
            to False, which means the data is returned as a list of tuples.

        Returns
        -------
        None or sequence
            None if is_write_query is True. A list of tuples or a pandas
            DataFrame (based on the dataframe input) if is_write_query is
            False.
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
            self.logger.error(
                ('Error executing {name} database query \'{query}\': {error}')
                .format(name=self.database, query=query, error=e))
            raise RedshiftClientError(
                ('Error executing {name} database query \'{query}\': {error}')
                .format(name=self.database, query=query, error=e)) from None
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
