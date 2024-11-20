import pytest

from base64 import b64encode
from nypl_py_utils.classes.kms_client import KmsClient, KmsClientError

_TEST_ENCRYPTED_VALUE = b64encode(b'test-encrypted-value')
_TEST_DECRYPTION = {
    'KeyId': 'test-key-id',
    'Plaintext': b'test-decrypted-value',
    'EncryptionAlgorithm': 'test-encryption-algorithm',
    'ResponseMetadata': {}
}


class TestKmsClient:

    @pytest.fixture
    def test_instance(self, mocker):
        mocker.patch('boto3.client')
        return KmsClient()

    def test_decrypt(self, test_instance):
        test_instance.kms_client.decrypt.return_value = _TEST_DECRYPTION
        assert test_instance.decrypt(
            _TEST_ENCRYPTED_VALUE) == 'test-decrypted-value'
        test_instance.kms_client.decrypt.assert_called_once_with(
            CiphertextBlob=b'test-encrypted-value')

    def test_base64_error(self, test_instance):
        with pytest.raises(KmsClientError):
            test_instance.decrypt('bad-b64')
