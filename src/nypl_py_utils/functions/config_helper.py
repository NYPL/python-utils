import json
import os
import yaml

from nypl_py_utils.classes.kms_client import KmsClient
from nypl_py_utils.functions.log_helper import create_log

logger = create_log('config_helper')


def load_env_file(run_type, file_string):
    """
    This method reads a YAML config file containing environment variables and
    loads them all into os.environ as strings. See _parse_yaml_dict for more.

    If the config file is divided into 'PLAINTEXT_VARIABLES' and
    'ENCRYPTED_VARIABLES' sections (see config/sample.yaml for an exmaple), the
    'ENCRYPTED_VARIABLES' variables will be decrypted first. Otherwise, all
    variables will be loaded as is.

    Parameters
        ----------
        run_type: str
            The name of the config file to use, e.g. 'sample'
        file_string: str
            The path to the config files with the filename as a variable to be
            interpolated, e.g. 'config/{}.yaml'
    """

    env_dict = None
    open_file = file_string.format(run_type)
    logger.info('Loading env file {}'.format(open_file))
    try:
        with open(open_file, 'r') as env_stream:
            try:
                env_dict = yaml.safe_load(env_stream)
            except yaml.YAMLError:
                raise ConfigHelperError(
                    'Invalid YAML file: {}'.format(open_file)) from None
    except FileNotFoundError:
        raise ConfigHelperError(
            'Could not find config file {}'.format(open_file)) from None

    if env_dict:
        if ('PLAINTEXT_VARIABLES' in env_dict
                or 'ENCRYPTED_VARIABLES' in env_dict):
            _parse_yaml_dict(env_dict.get('PLAINTEXT_VARIABLES', {}))

            kms_client = KmsClient()
            _parse_yaml_dict(env_dict.get(
                'ENCRYPTED_VARIABLES', {}), kms_client)
            kms_client.close()
        else:
            _parse_yaml_dict(env_dict)


def _parse_yaml_dict(yaml_dict, kms_client=None):
    """
    Loads YAML dict into os.environ. All values are stored as strings to match
    how AWS Lambda environment variables are stored. For list variables, the
    list is exported into os.environ as a json string.

    If kms_client is not empty, decrypts the variables first.

    Does not allow for sub-dictionaries.
    """
    for key, value in yaml_dict.items():
        if type(value) is dict:
            raise ConfigHelperError(
                'Found sub-dictionary in YAML config') from None
        elif type(value) is list:
            val = [kms_client.decrypt(v)
                   for v in value] if kms_client else value
            os.environ[key] = json.dumps(val)
        else:
            val = kms_client.decrypt(value) if kms_client else value
            os.environ[key] = str(val)


class ConfigHelperError(Exception):
    def __init__(self, message=None):
        self.message = message
        if message is not None:
            logger.error(message)

    def __str__(self):
        return self.message
