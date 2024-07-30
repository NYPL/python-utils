import pytest

from botocore.exceptions import ClientError
from datetime import datetime
from nypl_py_utils.classes.secrets_manager_client import (
    SecretsManagerClient, SecretsManagerClientError)

_TEST_RESPONSE = {
    'ARN': 'test_arn',
    'Name': 'test_secret',
    'VersionId': 'test_version',
    'SecretString': '{\n  "key1": "value1",\n  "key2": "value2"\n}',
    'VersionStages': ['AWSCURRENT'],
    'CreatedDate': datetime(2024, 1, 1, 1, 1, 1, 1),
    'ResponseMetadata': {
        'RequestId': 'test-request-id',
        'HTTPStatusCode': 200,
        'HTTPHeaders': {
            'x-amzn-requestid': 'test-request-id',
            'content-type': 'application/x-amz-json-1.1',
            'content-length': '155',
            'date': 'Mon, 1 Jan 2024 07:01:01 GMT'
        },
        'RetryAttempts': 0}
}


class TestSecretsManagerClient:

    @pytest.fixture
    def test_instance(self, mocker):
        mocker.patch('boto3.client')
        return SecretsManagerClient()

    def test_get_secret(self, test_instance):
        test_instance.secrets_manager_client.get_secret_value.return_value = \
            _TEST_RESPONSE
        assert test_instance.get_secret('test_secret') == {
            'key1': 'value1', 'key2': 'value2'}
        test_instance.secrets_manager_client.get_secret_value\
            .assert_called_once_with(SecretId='test_secret')

    def test_get_secret_non_json(self, test_instance):
        test_instance.secrets_manager_client.get_secret_value.return_value = \
            _TEST_RESPONSE
        assert test_instance.get_secret('test_secret', is_json=False) == (
            '{\n  "key1": "value1",\n  "key2": "value2"\n}')
        test_instance.secrets_manager_client.get_secret_value\
            .assert_called_once_with(SecretId='test_secret')

    def test_get_secret_error(self, test_instance):
        test_instance.secrets_manager_client.get_secret_value.side_effect = \
            ClientError({}, 'GetSecretValue')
        with pytest.raises(SecretsManagerClientError):
            test_instance.get_secret('test_secret')
