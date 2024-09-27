from base64 import b64decode
from io import StringIO
from nypl_py_utils.functions.log_helper import create_log
from paramiko import PKey, RSAKey, SSHClient
from paramiko.ssh_exception import SSHException


class SftpClient:
    """Client for interacting with a remote SSH server via SFTP"""

    def __init__(self, host, user, password=None, private_key_str=None):
        self.logger = create_log("sftp_client")
        self.host = host
        self.user = user
        self.password = password
        self.private_key_str = private_key_str
        self.ssh_client = SSHClient()

    def add_host_key(self, key_type, public_key):
        try:
            public_key = PKey.from_type_string(key_type, b64decode(public_key))
            self.ssh_client.get_host_keys().add(
                hostname=self.host, keytype=key_type, key=public_key
            )
        except Exception as e:
            self.logger.warning(f"Failed to load host key: {e}")

    def connect(self):
        """Connects to a remote server using SSH"""
        self.logger.info("Connecting to {}".format(self.host))
        pkey = None
        try:
            if self.private_key_str:
                pkey = RSAKey.from_private_key(StringIO(self.private_key_str))
            self.ssh_client.connect(self.host, username=self.user,
                                    password=self.password, pkey=pkey)
            self.sftp_conn = self.ssh_client.open_sftp()
        except SSHException as e:
            self.logger.error(
                "Error connecting to {host}: {error}".format(
                    host=self.host, error=e)
            )
            raise SftpClientError(
                "Error connecting to {host}: {error}".format(
                    host=self.host, error=e)
            ) from None

    def download(self, remote_path, local_path):
        """Downloads a file on the remote server to the local machine"""
        self.logger.info(
            "Downloading {remote} file as {local}".format(
                remote=remote_path, local=local_path
            )
        )
        try:
            self.sftp_conn.get(remote_path, local_path)
        except Exception as e:
            self.logger.error("Error downloading file: {}".format(e))
            self.close_connection()
            raise SftpClientError(
                "Error downloading file: {}".format(e)) from None

    def close_connection(self):
        """Closes the connection"""
        self.logger.debug("Closing connection to {}".format(self.host))
        self.sftp_conn.close()
        self.ssh_client.close()


class SftpClientError(Exception):
    def __init__(self, message=None):
        self.message = message
