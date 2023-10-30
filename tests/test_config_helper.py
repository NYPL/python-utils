import os
import pytest

from nypl_py_utils.functions.config_helper import (
    load_env_file, ConfigHelperError)

_TEST_VARIABLE_NAMES = [
    'TEST_STRING', 'TEST_INT', 'TEST_LIST', 'TEST_ENCRYPTED_VARIABLE_1',
    'TEST_ENCRYPTED_VARIABLE_2', 'TEST_ENCRYPTED_LIST']

_TEST_CONFIG_CONTENTS = \
    '''---
PLAINTEXT_VARIABLES:
    TEST_STRING: string-variable
    TEST_INT: 1
    TEST_LIST:
        - string-var
        - 2
ENCRYPTED_VARIABLES:
    TEST_ENCRYPTED_VARIABLE_1: test-encryption-1
    TEST_ENCRYPTED_VARIABLE_2: test-encryption-2
    TEST_ENCRYPTED_LIST:
        - test-encryption-3
        - test-encryption-4
...'''


class TestConfigHelper:

    def test_load_env_file(self, mocker):
        mock_kms_client = mocker.MagicMock()
        mock_kms_client.decrypt.side_effect = [
            'test-decryption-1', 'test-decryption-2', 'test-decryption-3',
            'test-decryption-4']
        mocker.patch('nypl_py_utils.functions.config_helper.KmsClient',
                     return_value=mock_kms_client)
        mock_file_open = mocker.patch(
            'builtins.open', mocker.mock_open(read_data=_TEST_CONFIG_CONTENTS))

        for key in _TEST_VARIABLE_NAMES:
            assert key not in os.environ
        load_env_file('test-env', 'test-path/{}.yaml')

        mock_file_open.assert_called_once_with('test-path/test-env.yaml', 'r')
        mock_kms_client.decrypt.assert_has_calls([
            mocker.call('test-encryption-1'), mocker.call('test-encryption-2'),
            mocker.call('test-encryption-3'), mocker.call('test-encryption-4')]
        )
        mock_kms_client.close.assert_called_once()
        assert os.environ['TEST_STRING'] == 'string-variable'
        assert os.environ['TEST_INT'] == '1'
        assert os.environ['TEST_LIST'] == '["string-var", 2]'
        assert os.environ['TEST_ENCRYPTED_VARIABLE_1'] == 'test-decryption-1'
        assert os.environ['TEST_ENCRYPTED_VARIABLE_2'] == 'test-decryption-2'
        assert os.environ['TEST_ENCRYPTED_LIST'] == \
            '["test-decryption-3", "test-decryption-4"]'

        for key in _TEST_VARIABLE_NAMES:
            if key in os.environ:
                del os.environ[key]

    def test_missing_file_error(self):
        with pytest.raises(ConfigHelperError):
            load_env_file('bad-env', 'bad-path/{}.yaml')

    def test_bad_yaml(self, mocker):
        mocker.patch(
            'builtins.open', mocker.mock_open(read_data='bad yaml: ['))
        with pytest.raises(ConfigHelperError):
            load_env_file('test-env', 'test-path/{}.not_yaml')
