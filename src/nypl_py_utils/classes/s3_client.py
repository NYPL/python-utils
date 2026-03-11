import boto3
import json
import os

from botocore.exceptions import ClientError
from io import BytesIO
from nypl_py_utils.functions.log_helper import create_log


class S3Client:
    """
    Client for fetching and setting an AWS S3 file.

    Takes as input the name of the S3 bucket. If fetching/setting a cache, also
    takes the cached resource.
    """

    def __init__(self, bucket, resource=None):
        self.logger = create_log('s3_client')
        self.bucket = bucket
        self.resource = resource

        try:
            self.s3_client = boto3.client(
                's3', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        except ClientError as e:
            error_msg = f'Could not create S3 client: {e}'
            self.logger.error(error_msg)
            raise S3ClientError(error_msg) from None

    def close(self):
        self.s3_client.close()

    def fetch_cache(self):
        """Fetches a JSON file from S3 and returns the resulting dictionary"""
        self.logger.info(
            f'Fetching {self.resource} from S3 bucket {self.bucket}')
        try:
            output_stream = BytesIO()
            self.s3_client.download_fileobj(
                self.bucket, self.resource, output_stream)
            return json.loads(output_stream.getvalue())
        except ClientError as e:
            error_msg = (
                f'Error retrieving {self.resource} from S3 bucket '
                f'{self.bucket}: {e}')
            self.logger.error(error_msg)
            raise S3ClientError(error_msg) from None

    def set_cache(self, state):
        """Writes a dictionary to JSON and uploads the resulting file to S3"""
        self.logger.info(
            f'Setting {self.resource} in S3 bucket {self.bucket} to {state}')
        try:
            input_stream = BytesIO(json.dumps(state).encode())
            self.s3_client.upload_fileobj(
                input_stream, self.bucket, self.resource)
        except ClientError as e:
            error_msg = (
                f'Error uploading {self.resource} to S3 bucket '
                f'{self.s3_bucket}: {e}')
            self.logger.error(error_msg)
            raise S3ClientError(error_msg) from None

    def upload_file(self, content, file_path):
        """
        Writes an arbitrary file to S3. Note that this will overwrite any
        existing file with the same name.

        Parameters
        ----------
        content: str
            The string that should be written to the file. Must be utf-8.
        file_path: str
            The full path of the file that should be written not including the
            bucket. Example: "subdirectory/example_file.csv"
        """
        self.logger.info(
            f'Writing {file_path} in S3 bucket {self.bucket}')
        try:
            input_stream = BytesIO(content.encode())
            self.s3_client.upload_fileobj(input_stream, self.bucket, file_path)
        except ClientError as e:
            error_msg = (
                f'Error uploading {file_path} to S3 bucket '
                f'{self.s3_bucket}: {e}')
            self.logger.error(error_msg)
            raise S3ClientError(error_msg) from None


class S3ClientError(Exception):
    def __init__(self, message=None):
        self.message = message
