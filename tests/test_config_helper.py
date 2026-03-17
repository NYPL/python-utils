import os
import pytest

from nypl_py_utils.functions.config_helper import (
    _parse_yaml_dict,
    load_env_file,
    ConfigHelperError
)

_TEST_CONFIG_CONTENTS_STRUCTURED = \
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

_TEST_CONFIG_CONTENTS_UNSTRUCTURED = \
    '''---
TEST_STRING: string-variable
TEST_INT: 1
TEST_LIST:
    - string-var
    - 2
TEST_ENCRYPTED_VARIABLE: test-encryption-1
...'''

_PLAINTEXT_DICT = {
    'TEST_STRING': 'string-variable', 'TEST_INT': 1,
    'TEST_LIST': ['string-var', 2]}

_ENCRYPTED_DICT = {
    'TEST_ENCRYPTED_VARIABLE_1': 'test-encryption-1',
    'TEST_ENCRYPTED_VARIABLE_2': 'test-encryption-2',
    'TEST_ENCRYPTED_LIST': ['test-encryption-3', 'test-encryption-4']}


class TestConfigHelper:

    def test_load_env_file_structured(self, mocker):
        mock_parser = mocker.patch(
            'nypl_py_utils.functions.config_helper._parse_yaml_dict')
        mock_file_open = mocker.patch(
            'builtins.open', mocker.mock_open(
                read_data=_TEST_CONFIG_CONTENTS_STRUCTURED))
        mock_kms_client = mocker.MagicMock()
        mocker.patch('nypl_py_utils.functions.config_helper.KmsClient',
                     return_value=mock_kms_client)

        load_env_file('test-env', 'test-path/{}.yaml')

        mock_file_open.assert_called_once_with('test-path/test-env.yaml', 'r')
        mock_parser.assert_has_calls([
            mocker.call(_PLAINTEXT_DICT),
            mocker.call(_ENCRYPTED_DICT, mock_kms_client)])
        mock_kms_client.close.assert_called_once()

    def test_load_env_file_unstructured(self, mocker):
        mock_parser = mocker.patch(
            'nypl_py_utils.functions.config_helper._parse_yaml_dict')
        mock_file_open = mocker.patch(
            'builtins.open', mocker.mock_open(
                read_data=_TEST_CONFIG_CONTENTS_UNSTRUCTURED))

        load_env_file('test-env', 'test-path/{}.yaml')

        mock_file_open.assert_called_once_with('test-path/test-env.yaml', 'r')
        mock_parser.assert_called_once_with(
            _PLAINTEXT_DICT | {'TEST_ENCRYPTED_VARIABLE': 'test-encryption-1'})

    def test_missing_file_error(self):
        with pytest.raises(ConfigHelperError):
            load_env_file('bad-env', 'bad-path/{}.yaml')

    def test_bad_yaml(self, mocker):
        mocker.patch(
            'builtins.open', mocker.mock_open(read_data='bad yaml: ['))
        with pytest.raises(ConfigHelperError):
            load_env_file('test-env', 'test-path/{}.not_yaml')

    def test_parse_yaml_dict_raw(self, mocker):
        _parse_yaml_dict(_PLAINTEXT_DICT)

        assert os.environ['TEST_STRING'] == 'string-variable'
        assert os.environ['TEST_INT'] == '1'
        assert os.environ['TEST_LIST'] == '["string-var", 2]'

        for key in _PLAINTEXT_DICT.keys():
            del os.environ[key]

    def test_parse_yaml_dict_encrypted(self, mocker):
        mock_kms_client = mocker.MagicMock()
        mock_kms_client.decrypt.side_effect = [
            'test-decryption-1', 'test-decryption-2', 'test-decryption-3',
            'test-decryption-4']

        _parse_yaml_dict(_ENCRYPTED_DICT, kms_client=mock_kms_client)

        mock_kms_client.decrypt.assert_has_calls([
            mocker.call('test-encryption-1'), mocker.call('test-encryption-2'),
            mocker.call('test-encryption-3'), mocker.call('test-encryption-4')]
        )
        assert os.environ['TEST_ENCRYPTED_VARIABLE_1'] == 'test-decryption-1'
        assert os.environ['TEST_ENCRYPTED_VARIABLE_2'] == 'test-decryption-2'
        assert os.environ['TEST_ENCRYPTED_LIST'] == \
            '["test-decryption-3", "test-decryption-4"]'

        for key in _ENCRYPTED_DICT.keys():
            del os.environ[key]

    def test_parse_yaml_dict_sub_dictionary(self, mocker):
        with pytest.raises(ConfigHelperError):
            _parse_yaml_dict({'1': {'2': '3'}})
