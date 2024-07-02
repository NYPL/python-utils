import boto3
import os
import time

from botocore.exceptions import ClientError
from nypl_py_utils.functions.log_helper import create_log


class KinesisClient:
    """
    Client for sending records to AWS Kinesis.

    Takes as input the ARN of the Kinesis stream to which records should be
    sent, how many records should be sent at once, and how many times in a row
    records should try and fail to be sent to Kinesis before an error is
    thrown. Kinesis supports up to 500 records per batch.
    """

    def __init__(self, stream_arn, batch_size, max_retries=5):
        self.logger = create_log('kinesis_client')
        self.stream_arn = stream_arn
        self.batch_size = batch_size
        self.max_retries = max_retries

        try:
            self.kinesis_client = boto3.client(
                'kinesis', region_name=os.environ.get('AWS_REGION',
                                                      'us-east-1'))
        except ClientError as e:
            self.logger.error(
                'Could not create Kinesis client: {err}'.format(err=e))
            raise KinesisClientError(
                'Could not create Kinesis client: {err}'.format(err=e)
            ) from None

    def close(self):
        self.kinesis_client.close()

    def send_records(self, records):
        """
        Sends list of records (usually represented as Avro-encoded byte
        strings) to Kinesis in batches of size self.batch_size. Kinesis can
        only handle 1000 records per second, so this method waits a second
        between each 1000 records.
        """
        records_sent_since_pause = 0
        for i in range(0, len(records), self.batch_size):
            encoded_batch = records[i:i + self.batch_size]
            kinesis_records = [{'Data': record, 'PartitionKey':
                                str(int(time.time() * 1000000000))}
                               for record in encoded_batch]

            if records_sent_since_pause + len(encoded_batch) > 1000:
                records_sent_since_pause = 0
                time.sleep(1)
            self._send_kinesis_format_records(kinesis_records, 1)
            records_sent_since_pause += len(encoded_batch)

    def _send_kinesis_format_records(self, kinesis_records, call_count):
        """
        Sends list of records in Kinesis format to Kinesis. This method is
        recursively called when Kinesis fails to retrieve some of the records.
        """
        if call_count > self.max_retries:
            self.logger.error(
                'Failed to send records to Kinesis {} times in a row'.format(
                    call_count-1))
            raise KinesisClientError(
                'Failed to send records to Kinesis {} times in a row'.format(
                    call_count-1)) from None

        try:
            self.logger.info(
                'Sending ({count}) records to {arn} Kinesis stream'.format(
                    count=len(kinesis_records), arn=self.stream_arn))
            response = self.kinesis_client.put_records(
                Records=kinesis_records, StreamARN=self.stream_arn)
            if response['FailedRecordCount'] > 0:
                self.logger.warning(
                    'Failed to send {} records to Kinesis'.format(
                        response['FailedRecordCount']))
                failed_records = []
                for i in range(len(response['Records'])):
                    if 'ErrorCode' in response['Records'][i]:
                        failed_records.append(kinesis_records[i])
                self._send_kinesis_format_records(failed_records, call_count+1)
        except ClientError as e:
            self.logger.error(
                'Error sending records to Kinesis: {}'.format(e))
            raise KinesisClientError(
                'Error sending records to Kinesis: {}'.format(e)) from None


class KinesisClientError(Exception):
    def __init__(self, message=None):
        self.message = message
