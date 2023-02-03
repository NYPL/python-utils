import boto3
import os

from base64 import b64decode
from binascii import Error as base64Error
from botocore.exceptions import ClientError
from nypl_py_utils.functions.log_helper import create_log

logger = create_log('kms_helper')


def decrypt(encrypted_text):
    """This method creates a KMS client and calls `decrypt_with_kms_client`"""

    logger.debug('Creating new KMS client')
    try:
        kms_client = boto3.client(
            'kms', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    except ClientError as e:
        logger.error('Could not create KMS client: {err}'.format(err=e))
        raise KmsHelperError(
            'Could not create KMS client: {err}'.format(err=e)) from None

    return decrypt_with_kms_client(encrypted_text, kms_client)


def decrypt_with_kms_client(encrypted_text, kms_client):
    """
    This method takes a base 64 KMS-encoded string and uses the input KMS
    client to decrypt it into a usable string.
    """

    logger.debug('Decrypting \'{}\''.format(encrypted_text))
    try:
        decoded_text = b64decode(encrypted_text)
        return kms_client.decrypt(CiphertextBlob=decoded_text)[
            'Plaintext'].decode('utf-8')
    except (ClientError, base64Error, TypeError) as e:
        logger.error('Could not decrypt \'{val}\': {err}'.format(
            val=encrypted_text, err=e))
        raise KmsHelperError('Could not decrypt \'{val}\': {err}'.format(
            val=encrypted_text, err=e)) from None


class KmsHelperError(Exception):
    def __init__(self, message=None):
        self.message = message
