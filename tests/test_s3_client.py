import json
import pytest

from nypl_py_utils.classes.s3_client import S3Client

_TEST_STATE = {"key1": "val1", "key2": "val2", "key3": "val3"}


class TestS3Client:

    @pytest.fixture
    def test_instance(self, mocker):
        mocker.patch("boto3.client")
        return S3Client("test_s3_bucket", "test_s3_resource")

    def test_fetch_cache(self, test_instance):
        def mock_download(bucket, resource, stream):
            assert bucket == "test_s3_bucket"
            assert resource == "test_s3_resource"
            stream.write(json.dumps(_TEST_STATE).encode())

        test_instance.s3_client.download_fileobj.side_effect = mock_download
        assert test_instance.fetch_cache() == _TEST_STATE

    def test_set_cache(self, test_instance):
        test_instance.set_cache(_TEST_STATE)
        arguments = test_instance.s3_client.upload_fileobj.call_args.args
        assert arguments[0].getvalue() == json.dumps(_TEST_STATE).encode()
        assert arguments[1] == "test_s3_bucket"
        assert arguments[2] == "test_s3_resource"

    def test_upload_file_encoded(self, test_instance, mocker):
        test_instance.upload_file("test_content", "test_filename.txt")
        arguments = test_instance.s3_client.upload_fileobj.call_args.args
        expected_content = "test_content".encode("utf-8")

        # check that the content is encoded as utf-8 before being sent to S3
        assert arguments[0].getvalue() == expected_content
        assert arguments[1] == "test_s3_bucket"
        assert arguments[2] == "test_filename.txt"

    def test_upload_file_binary(self, test_instance):
        binary_content = b"PAR1\x00\x01\xff\xfe"
        test_instance.upload_file(binary_content, "test_filename.parquet")
        arguments = test_instance.s3_client.upload_fileobj.call_args.args

        # check bytes aren't re-encoded; they should reach S3 as-is
        assert arguments[0].getvalue() == binary_content
        assert arguments[1] == "test_s3_bucket"
        assert arguments[2] == "test_filename.parquet"
