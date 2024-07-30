import boto3
import json
import os

from botocore.exceptions import ClientError
from nypl_py_utils.functions.log_helper import create_log


class SecretsManagerClient:
    """Client for interacting with AWS Secrets Manager"""

    def __init__(self):
        self.logger = create_log('secrets_manager_client')

        try:
            self.secrets_manager_client = boto3.client(
                'secretsmanager', region_name=os.environ.get('AWS_REGION',
                                                             'us-east-1'))
        except ClientError as e:
            self.logger.error(
                'Could not create Secrets Manager client: {err}'.format(
                    err=e))
            raise SecretsManagerClientError(
                'Could not create Secrets Manager client: {err}'.format(
                    err=e)) from None

    def close(self):
        self.secrets_manager_client.close()

    def get_secret(self, secret_name, is_json=True):
        """
        Retrieves secret with the given name from the Secrets Manager.

        Parameters
        ----------
        secret_name: str
            The name of the secret to retrieve
        is_json: bool, optional
            Whether the value of the secret is a JSON string that should be
            returned as a dictionary

        Returns
        -------
        dict or str
            Dictionary if `is_json` is True; string if `is_json` is False
        """
        self.logger.debug('Retrieving \'{}\' from Secrets Manager'.format(
            secret_name))
        try:
            response = self.secrets_manager_client.get_secret_value(
                SecretId=secret_name)
            if is_json:
                return json.loads(response['SecretString'])
            else:
                return response['SecretString']
        except ClientError as e:
            self.logger.error(
                ('Could not retrieve \'{secret}\' from Secrets Manager: {err}')
                .format(secret=secret_name, err=e))
            raise SecretsManagerClientError(
                ('Could not retrieve \'{secret}\' from Secrets Manager: {err}')
                .format(secret=secret_name, err=e)) from None


class SecretsManagerClientError(Exception):
    def __init__(self, message=None):
        self.message = message
