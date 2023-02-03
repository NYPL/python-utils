import os
import pytest

from nypl_py_utils.functions.config_helper import (
    load_env_file, ConfigHelperError)

_TEST_VARIABLE_NAMES = ['TEST_STRING', 'TEST_INT', 'TEST_ENCRYPTED_VARIABLE_1',
                        'TEST_ENCRYPTED_VARIABLE_2']
_TEST_CONFIG_CONTENTS = \
    '''---
PLAINTEXT_VARIABLES:
    TEST_STRING: string-variable
    TEST_INT: 1
ENCRYPTED_VARIABLES:
    TEST_ENCRYPTED_VARIABLE_1: test-encryption-1
    TEST_ENCRYPTED_VARIABLE_2: test-encryption-2
...'''


class TestConfigHelper:

    def test_load_env_file(self, mocker):
        os.environ['AWS_REGION'] = 'test-aws-region'
        mock_file_open = mocker.patch(
            'builtins.open', mocker.mock_open(read_data=_TEST_CONFIG_CONTENTS))
        mock_kms_client = mocker.MagicMock()
        mock_boto3_client = mocker.patch(
            'boto3.client', return_value=mock_kms_client)
        mock_decryption = mocker.patch(
            'nypl_py_utils.functions.config_helper.decrypt_with_kms_client',
            side_effect=['test-decryption-1', 'test-decryption-2'])

        for key in _TEST_VARIABLE_NAMES:
            assert key not in os.environ
        load_env_file('test-env', 'test-path/{}.yaml')

        mock_file_open.assert_called_once_with('test-path/test-env.yaml', 'r')
        mock_boto3_client.assert_called_once_with(
            'kms', region_name='test-aws-region')
        mock_decryption.assert_has_calls([
            mocker.call('test-encryption-1', mock_kms_client),
            mocker.call('test-encryption-2', mock_kms_client)])
        assert os.environ['TEST_STRING'] == 'string-variable'
        assert os.environ['TEST_INT'] == '1'
        assert os.environ['TEST_ENCRYPTED_VARIABLE_1'] == 'test-decryption-1'
        assert os.environ['TEST_ENCRYPTED_VARIABLE_2'] == 'test-decryption-2'

        for key in _TEST_VARIABLE_NAMES:
            if key in os.environ:
                del os.environ[key]
        del os.environ['AWS_REGION']

    def test_missing_file_error(self):
        with pytest.raises(ConfigHelperError):
            load_env_file('bad-env', 'bad-path/{}.yaml')

    def test_bad_yaml(self, mocker):
        mocker.patch(
            'builtins.open', mocker.mock_open(read_data='bad yaml: ['))
        with pytest.raises(ConfigHelperError):
            load_env_file('test-env', 'test-path/{}.not_yaml')
