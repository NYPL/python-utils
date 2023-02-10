import boto3
import os

from base64 import b64decode
from binascii import Error as base64Error
from botocore.exceptions import ClientError
from nypl_py_utils.functions.log_helper import create_log


class KmsClient:
    """Client for interacting with a KMS client"""

    def __init__(self):
        self.logger = create_log('kms_client')

        try:
            self.kms_client = boto3.client(
                'kms', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        except ClientError as e:
            self.logger.error(
                'Could not create KMS client: {err}'.format(err=e))
            raise KmsClientError(
                'Could not create KMS client: {err}'.format(err=e)) from None

    def close(self):
        self.kms_client.close()

    def decrypt(self, encrypted_text):
        """
        This method takes a base 64 KMS-encoded string and uses the KMS client
        to decrypt it into a usable string.
        """
        self.logger.debug('Decrypting \'{}\''.format(encrypted_text))
        try:
            decoded_text = b64decode(encrypted_text)
            return self.kms_client.decrypt(CiphertextBlob=decoded_text)[
                'Plaintext'].decode('utf-8')
        except (ClientError, base64Error, TypeError) as e:
            self.logger.error('Could not decrypt \'{val}\': {err}'.format(
                val=encrypted_text, err=e))
            raise KmsClientError('Could not decrypt \'{val}\': {err}'.format(
                val=encrypted_text, err=e)) from None


class KmsClientError(Exception):
    def __init__(self, message=None):
        self.message = message
