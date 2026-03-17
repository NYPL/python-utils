import snowflake.connector as sc

from nypl_py_utils.functions.log_helper import create_log


class SnowflakeClient:
    """Client for managing connections to Snowflake"""

    def __init__(self, account, user, password, warehouse=None):
        self.logger = create_log('snowflake_client')
        self.conn = None
        self.account = account
        self.user = user
        self.password = password
        self.warehouse = warehouse

    def connect(self, **kwargs):
        """
        Connects to a Snowflake database using the given credentials. If
        warehouse parameter is None, uses the default warehouse for the user.

        Parameters
        ----------
        kwargs:
            All possible arguments (such as timeouts) can be found here:
            https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-api#connect
        """
        self.logger.info('Connecting to Snowflake')
        try:
            self.conn = sc.connect(
                account=self.account,
                user=self.user,
                password=self.password,
                warehouse=self.warehouse,
                **kwargs)
        except Exception as e:
            raise SnowflakeClientError(
                f'Error connecting to Snowflake: {e}') from None

    def execute_query(self, query, **kwargs):
        """
        Executes an arbitrary query against the given database connection.

        Note that:
            1) All results will be fetched by default, so this method is not
                suitable if you do not want to load all rows into memory
            2) AUTOCOMMIT is on by default, so this method is not suitable if
               you want to execute multiple queries in a single transaction
            3) This method can be used for both read and write queries, but
               it's not optimized for writing -- there is no parameter binding
               or executemany support, and the return value for write queries
               can be unpredictable.

        Parameters
        ----------
        kwargs:
            All possible arguments (such as timeouts) can be found here:
            https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-api#execute

        Returns
        -------
        sequence
            A list of tuples
        """
        self.logger.info('Querying database')
        cursor = self.conn.cursor()
        try:
            try:
                cursor.execute(query, **kwargs)
                return cursor.fetchall()
            except Exception:
                raise
            finally:
                cursor.close()
        except Exception as e:
            # If there was an error, also close the database connection
            self.close_connection()

            short_q = str(query)
            if len(short_q) > 2500:
                short_q = short_q[:2497] + "..."
            raise SnowflakeClientError(
                f'Error executing Snowflake query {short_q}: {e}', self.logger
            ) from None

    def close_connection(self):
        """Closes the connection"""
        self.logger.info('Closing Snowflake connection')
        self.conn.close()


class SnowflakeClientError(Exception):
    def __init__(self, message='', logger=None):
        self.message = message
        if logger is not None:
            logger.error(message)

    def __str__(self):
        return self.message
