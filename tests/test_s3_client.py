import json
import pytest

from nypl_py_utils.classes.s3_client import S3Client

_TEST_STATE = {'key1': 'val1', 'key2': 'val2', 'key3': 'val3'}


class TestS3Client:

    @pytest.fixture
    def test_instance(self, mocker):
        mocker.patch('boto3.client')
        return S3Client('test_s3_bucket', 'test_s3_resource')

    def test_fetch_cache(self, test_instance):
        def mock_download(bucket, resource, stream):
            assert bucket == 'test_s3_bucket'
            assert resource == 'test_s3_resource'
            stream.write(json.dumps(_TEST_STATE).encode())

        test_instance.s3_client.download_fileobj.side_effect = mock_download
        assert test_instance.fetch_cache() == _TEST_STATE

    def test_set_cache(self, test_instance):
        test_instance.set_cache(_TEST_STATE)
        arguments = test_instance.s3_client.upload_fileobj.call_args.args
        assert arguments[0].getvalue() == json.dumps(_TEST_STATE).encode()
        assert arguments[1] == 'test_s3_bucket'
        assert arguments[2] == 'test_s3_resource'
