import os
import pytest

from base64 import b64encode
from nypl_py_utils.functions.kms_helper import (
    decrypt, decrypt_with_kms_client, KmsHelperError)

_TEST_ENCRYPTED_VALUE = b64encode(b'test-encrypted-value')
_TEST_DECRYPTION = {
    'KeyId': 'test-key-id',
    'Plaintext': b'test-decrypted-value',
    'EncryptionAlgorithm': 'test-encryption-algorithm',
    'ResponseMetadata': {}
}


class TestKmsHelper:

    @pytest.fixture
    def mock_kms_client(self, mocker):
        mock_kms_client = mocker.MagicMock()
        mock_kms_client.decrypt.return_value = _TEST_DECRYPTION
        return mock_kms_client

    def test_decrypt(self, mock_kms_client, mocker):
        os.environ['AWS_REGION'] = 'test-aws-region'
        mock_boto3_method = mocker.patch('boto3.client')
        mocker.patch(
            'nypl_py_utils.functions.kms_helper.decrypt_with_kms_client',
            return_value='test-decrypted-value')

        assert decrypt(_TEST_ENCRYPTED_VALUE) == 'test-decrypted-value'
        mock_boto3_method.assert_called_once_with(
            'kms', region_name='test-aws-region')
        del os.environ['AWS_REGION']

    def test_decrypt_with_kms_client(self, mock_kms_client):
        assert decrypt_with_kms_client(
            _TEST_ENCRYPTED_VALUE, mock_kms_client) == 'test-decrypted-value'
        mock_kms_client.decrypt.called_once_with(
            CiphertextBlob=b'test-encrypted-value')

    def test_base64_error(self, mock_kms_client):
        with pytest.raises(KmsHelperError):
            decrypt_with_kms_client('bad-b64', mock_kms_client)
