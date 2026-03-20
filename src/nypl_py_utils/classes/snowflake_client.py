import snowflake.connector as sc

from nypl_py_utils.functions.log_helper import create_log


class SnowflakeClient:
    """Client for managing connections to Snowflake"""

    def __init__(self, account, user, private_key=None, password=None):
        self.logger = create_log('snowflake_client')
        if (password is None) == (private_key is None):
            raise SnowflakeClientError(
                'Either password or private key must be set (but not both)',
                self.logger
            ) from None

        self.conn = None
        self.account = account
        self.user = user
        self.private_key = private_key
        self.password = password

    def connect(self, mfa_code=None, **kwargs):
        """
        Connects to Snowflake using the given credentials. If you're connecting
        locally, you should be using the password and mfa_code. If the
        connection is for production code, a private_key should be set up.

        Parameters
        ----------
        mfa_code: str, optional
            The six-digit MFA code. Only necessary for connecting as a human
            user.
        kwargs:
            All possible arguments (such as which warehouse to use or how
            long to wait before timing out) can be found here:
            https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-api#connect
        """
        self.logger.info('Connecting to Snowflake')
        if self.private_key is not None:
            try:
                self.conn = sc.connect(
                    account=self.account,
                    user=self.user,
                    private_key=self.private_key,
                    **kwargs)
            except Exception as e:
                raise SnowflakeClientError(
                    f'Error connecting to Snowflake: {e}', self.logger
                ) from None
        else:
            if mfa_code is None:
                raise SnowflakeClientError(
                    'When using a password, an MFA code must also be provided',
                    self.logger
                ) from None

            pw = self.password + mfa_code
            try:
                self.conn = sc.connect(
                    account=self.account,
                    user=self.user,
                    password=pw,
                    passcode_in_password=True,
                    **kwargs)
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
