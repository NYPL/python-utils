import snowflake.connector as sc

from nypl_py_utils.functions.log_helper import create_log


class SnowflakeClient:
    """Client for managing connections to Snowflake"""

    def __init__(self, connection_params):
        """
        See the `connect` method below for what `connection_params` should
        look like
        """
        self.logger = create_log('snowflake_client')
        self.connection_params = connection_params
        self.conn = None

    def connect(self):
        """
        Connects to Snowflake using the given connection parameters. In practice, there
        are likely two sets of parameters that will be used:
            1. Local development: `connection_name` and `private_key_file_pwd`. This
            method requires a `connections.toml` file with a matching `connection_name`
            connection.
            2. Production code: `account`, `user`, and `private_key`

        All possible parameters can be found here:
        https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-api#connect
        """
        self.logger.info('Connecting to Snowflake')
        try:
            self.conn = sc.connect(**self.connection_params)
        except Exception as e:
            raise SnowflakeClientError(
                f'Error connecting to Snowflake: {e}', self.logger
            ) from None

    def execute_query(self, query, **kwargs):
        """
        Executes an arbitrary query against the given connection.

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
        query: str
            The SQL query to execute
        kwargs:
            All possible arguments (such as timeouts) can be found here:
            https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-api#execute

        Returns
        -------
        sequence
            A list of tuples
        """
        self.logger.info('Querying Snowflake')
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
            # If there was an error, also close the connection
            self.close_connection()

            short_q = str(query)
            if len(short_q) > 2500:
                short_q = short_q[:2497] + '...'
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
