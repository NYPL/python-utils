import boto3
import os
import yaml

from base64 import b64decode
from binascii import Error as base64Error
from botocore.exceptions import ClientError
from log_helper import create_log

logger = create_log('config_helper')


def load_env_file(run_type, file_string):
    """
    This method loads a YAML config file containing environment variables,
    decrypts whichever are encrypted, and puts them all into os.environ.

    It requires the YAML file to be split into a 'PLAINTEXT_VARIABLES' section
    and a 'ENCRYPTED_VARIABLES' section.
    """

    env_dict = None
    open_file = file_string.format(run_type)
    logger.info('Loading env file {}'.format(open_file))
    try:
        with open(open_file, 'r') as env_stream:
            try:
                env_dict = yaml.safe_load(env_stream)
            except yaml.YAMLError as err:
                logger.error('Invalid YAML file: {}'.format(open_file))
                raise err
    except FileNotFoundError:
        logger.error('Could not find config file {}'.format(open_file))
        raise ConfigHelperError(
            'Could not find config file {}'.format(open_file)) from None

    if env_dict:
        for key, value in env_dict.get('PLAINTEXT_VARIABLES', {}).items():
            os.environ[key] = str(value)

        kms_client = boto3.client(
            'kms', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        for key, value in env_dict.get('ENCRYPTED_VARIABLES', {}).items():
            os.environ[key] = _decrypt_env_var(value, kms_client)


def _decrypt_env_var(var, kms_client):
    """
    This method takes a KMS-encoded environment variable and a KMS client and
    decrypts the variable into a usable value.
    """

    logger.debug('Decrypting environment variable with value {}'.format(var))
    try:
        decoded = b64decode(var)
        return kms_client.decrypt(CiphertextBlob=decoded)['Plaintext'].decode(
            'utf-8')
    except (ClientError, base64Error, TypeError) as e:
        logger.error(
            'Could not decrypt \'{val}\': {err}'.format(val=var, err=e))
        raise ConfigHelperError(
            'Could not decrypt \'{val}\': {err}'.format(val=var, err=e)
        ) from None


class ConfigHelperError(Exception):
    def __init__(self, message=None):
        self.message = message
