import json
import os
import yaml

from nypl_py_utils.classes.kms_client import KmsClient
from nypl_py_utils.functions.log_helper import create_log

logger = create_log('config_helper')


def load_env_file(run_type, file_string):
    """
    This method loads a YAML config file containing environment variables,
    decrypts whichever are encrypted, and puts them all into os.environ as
    strings. For a YAML variable containing a list of values, the list is
    exported into os.environ as a json string and should be loaded as such.

    It requires the YAML file to be split into a 'PLAINTEXT_VARIABLES' section
    and an 'ENCRYPTED_VARIABLES' section. See config/sample.yaml for an example
    config file.

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
                logger.error('Invalid YAML file: {}'.format(open_file))
                raise ConfigHelperError(
                    'Invalid YAML file: {}'.format(open_file)) from None
    except FileNotFoundError:
        logger.error('Could not find config file {}'.format(open_file))
        raise ConfigHelperError(
            'Could not find config file {}'.format(open_file)) from None

    if env_dict:
        for key, value in env_dict.get('PLAINTEXT_VARIABLES', {}).items():
            if type(value) is list:
                os.environ[key] = json.dumps(value)
            else:
                os.environ[key] = str(value)

        kms_client = KmsClient()
        for key, value in env_dict.get('ENCRYPTED_VARIABLES', {}).items():
            if type(value) is list:
                decrypted_list = [kms_client.decrypt(v) for v in value]
                os.environ[key] = json.dumps(decrypted_list)
            else:
                os.environ[key] = kms_client.decrypt(value)
        kms_client.close()


class ConfigHelperError(Exception):
    def __init__(self, message=None):
        self.message = message
