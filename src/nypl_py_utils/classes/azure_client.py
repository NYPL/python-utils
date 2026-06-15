import mssql_python
import pandas as pd
import time

from nypl_py_utils.functions.log_helper import create_log


class AzureClient:
    """Class for managing connections to a Microsoft Azure SQL database"""

    def __init__(self, server, database, user, password):
        self.logger = create_log("azure_client")
        self.server = server
        self.database = database
        self.user = user
        self.password = password
        self.conn = None

    def connect(self, retry_count=0, backoff_factor=5):
        """
        Connects to an Azure database using the given credentials.

        Parameters
        ----------
        retry_count: int, optional
            The number of times to retry connecting before throwing an error.
            By default no retry occurs.
        backoff_factor: int, optional
            The backoff factor when retrying. The amount of time to wait before
            retrying is backoff_factor ** number_of_retries_made.
        """
        self.logger.info(f"Connecting to {self.database} database...")

        # Close any existing connection first so reconnecting doesn't leak it
        self.close_connection()

        attempt_count = 0
        while attempt_count <= retry_count:
            try:
                try:
                    connection_string = (
                        f"Server={self.server};"
                        f"Database={self.database};"
                        f"UID={self.user};"
                        f"PWD={self.password};"
                        f"Encrypt=yes;"
                    )
                    self.conn = mssql_python.connect(
                        connection_str=connection_string,
                        timeout=30,
                    )
                    self.conn.setencoding(encoding="utf-8")
                    self.conn.setdecoding(
                        sqltype=mssql_python.SQL_WCHAR, encoding="utf-8"
                    )
                    return
                except (mssql_python.InterfaceError,
                        mssql_python.OperationalError):
                    if attempt_count < retry_count:
                        self.logger.info("Failed to connect — retrying")
                        time.sleep(backoff_factor**attempt_count)
                        attempt_count += 1
                    else:
                        raise
            except Exception as e:
                msg = f"Error connecting to {self.database} database: {e}"
                self.logger.error(msg)
                raise AzureClientError(msg) from e

    def execute_query(self, query: str, params=None, dataframe=False):
        """
        Executes an arbitrary SQL read query against the database.

        Parameters
        ----------
        query: str
            The query to execute, assumed to be a read query
        params: tuple or list, optional
            The parameters to pass into the query, if any. Defaults to None.
        dataframe: bool, optional
            Whether the data will be returned as a pandas DataFrame. Defaults
            to False, which means the data is returned as a list of tuples.

        Returns
        -------
        None or sequence
            A list of tuples or a pandas DataFrame (based on the `dataframe`
            input)
        """
        if not self.conn:
            msg = "No active database connection"
            self.logger.error(msg)
            raise AzureClientError(msg)

        cursor = self.conn.cursor()
        try:
            try:
                if params is not None:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                if dataframe:
                    columns = [col[0] for col in cursor.description]
                    return pd.DataFrame.from_records(
                        cursor.fetchall(), columns=columns)
                return cursor.fetchall()
            finally:
                cursor.close()
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            self.close_connection()

            msg = f"Error executing {self.database} query '{query}': {e}"
            self.logger.error(msg)
            raise AzureClientError(msg) from e

    def close_connection(self):
        """Closes the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.logger.info(f"Connection to {self.database} closed.")


class AzureClientError(Exception):
    """Custom exception for AzureClient errors"""

    def __init__(self, message=None):
        super().__init__(message)
        self.message = message
