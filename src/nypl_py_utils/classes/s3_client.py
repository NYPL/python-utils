import boto3
import json
import os

from botocore.exceptions import ClientError
from io import BytesIO
from nypl_py_utils.functions.log_helper import create_log


class S3Client:
    """
    Client for fetching and setting an AWS S3 file.

    Takes as input the name of the S3 bucket and resource to be fetched/set.
    """

    def __init__(self, bucket, resource):
        self.logger = create_log('s3_client')
        self.bucket = bucket
        self.resource = resource

        try:
            self.s3_client = boto3.client(
                's3', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        except ClientError as e:
            self.logger.error(
                'Could not create S3 client: {err}'.format(err=e))
            raise S3ClientError(
                'Could not create S3 client: {err}'.format(err=e)) from None

    def close(self):
        self.s3_client.close()

    def fetch_cache(self):
        """Fetches a JSON file from S3 and returns the resulting dictionary"""
        self.logger.info('Fetching {file} from S3 bucket {bucket}'.format(
            file=self.resource, bucket=self.bucket))
        try:
            output_stream = BytesIO()
            self.s3_client.download_fileobj(
                self.bucket, self.resource, output_stream)
            return json.loads(output_stream.getvalue())
        except ClientError as e:
            self.logger.error(
                'Error retrieving {file} from S3 bucket {bucket}: {error}'
                .format(file=self.resource, bucket=self.bucket, error=e))
            raise S3ClientError(
                'Error retrieving {file} from S3 bucket {bucket}: {error}'
                .format(file=self.resource, bucket=self.bucket, error=e)
            ) from None

    def set_cache(self, state):
        """Writes a dictionary to JSON and uploads the resulting file to S3"""
        self.logger.info(
            'Setting {file} in S3 bucket {bucket} to {state}'.format(
                file=self.resource, bucket=self.bucket, state=state))
        try:
            input_stream = BytesIO(json.dumps(state).encode())
            self.s3_client.upload_fileobj(
                input_stream, self.bucket, self.resource)
        except ClientError as e:
            self.logger.error(
                'Error uploading {file} to S3 bucket {bucket}: {error}'
                .format(file=self.resource, bucket=self.bucket, error=e))
            raise S3ClientError(
                'Error uploading {file} to S3 bucket {bucket}: {error}'
                .format(file=self.resource, bucket=self.bucket, error=e)
            ) from None


class S3ClientError(Exception):
    def __init__(self, message=None):
        self.message = message
