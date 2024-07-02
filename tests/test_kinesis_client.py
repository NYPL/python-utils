import pytest

from freezegun import freeze_time
from nypl_py_utils.classes.kinesis_client import (
    KinesisClient, KinesisClientError)

_TEST_DATETIME_KEY = '1672531200000000000'
_TEST_KINESIS_RECORDS = [
    {'Data': b'a', 'PartitionKey': _TEST_DATETIME_KEY},
    {'Data': b'b', 'PartitionKey': _TEST_DATETIME_KEY},
    {'Data': b'c', 'PartitionKey': _TEST_DATETIME_KEY},
    {'Data': b'd', 'PartitionKey': _TEST_DATETIME_KEY},
    {'Data': b'e', 'PartitionKey': _TEST_DATETIME_KEY}
]


@freeze_time('2023-01-01')
class TestKinesisClient:

    @pytest.fixture
    def test_instance(self, mocker):
        mocker.patch('boto3.client')
        return KinesisClient('test_stream_arn', 2)

    def test_send_records(self, test_instance, mocker):
        MOCK_RECORDS = [b'a', b'b', b'c', b'd', b'e']
        mocked_send_method = mocker.patch(
            'nypl_py_utils.classes.kinesis_client.KinesisClient._send_kinesis_format_records')  # noqa: E501
        mock_sleep = mocker.patch('time.sleep', return_value=None)

        test_instance.send_records(MOCK_RECORDS)
        mocked_send_method.assert_has_calls([
            mocker.call([_TEST_KINESIS_RECORDS[0],
                        _TEST_KINESIS_RECORDS[1]], 1),
            mocker.call([_TEST_KINESIS_RECORDS[2],
                        _TEST_KINESIS_RECORDS[3]], 1),
            mocker.call([_TEST_KINESIS_RECORDS[4]], 1)])
        mock_sleep.assert_not_called()

    def test_send_records_with_pause(self, mocker):
        mocker.patch('boto3.client')
        test_instance = KinesisClient('test_stream_arn', 500)

        MOCK_RECORDS = [b'a'] * 2200
        mocked_send_method = mocker.patch(
            'nypl_py_utils.classes.kinesis_client.KinesisClient._send_kinesis_format_records')  # noqa: E501
        mock_sleep = mocker.patch('time.sleep', return_value=None)

        test_instance.send_records(MOCK_RECORDS)
        mocked_send_method.assert_has_calls([
            mocker.call([_TEST_KINESIS_RECORDS[0]]*500, 1),
            mocker.call([_TEST_KINESIS_RECORDS[0]]*500, 1),
            mocker.call([_TEST_KINESIS_RECORDS[0]]*500, 1),
            mocker.call([_TEST_KINESIS_RECORDS[0]]*500, 1),
            mocker.call([_TEST_KINESIS_RECORDS[0]]*200, 1)])
        assert mock_sleep.call_count == 2

    def test_send_kinesis_format_records(self, test_instance):
        test_instance.kinesis_client.put_records.return_value = {
            'FailedRecordCount': 0}

        test_instance._send_kinesis_format_records(_TEST_KINESIS_RECORDS, 1)
        test_instance.kinesis_client.put_records.assert_called_once_with(
            Records=_TEST_KINESIS_RECORDS, StreamARN='test_stream_arn')

    def test_send_kinesis_format_records_with_failures(
            self, test_instance, mocker):
        test_instance.kinesis_client.put_records.side_effect = [
            {'FailedRecordCount': 2, 'Records': [
                'record0', {'ErrorCode': 1},
                'record2', {'ErrorCode': 3},
                'record4']},
            {'FailedRecordCount': 0}]

        test_instance._send_kinesis_format_records(_TEST_KINESIS_RECORDS, 1)
        test_instance.kinesis_client.put_records.assert_has_calls([
            mocker.call(Records=_TEST_KINESIS_RECORDS,
                        StreamARN='test_stream_arn'),
            mocker.call(Records=[_TEST_KINESIS_RECORDS[1],
                                 _TEST_KINESIS_RECORDS[3]],
                        StreamARN='test_stream_arn')])

    def test_send_kinesis_format_records_with_repeating_failures(
            self, test_instance, mocker):
        test_instance.kinesis_client.put_records.side_effect = [
            {'FailedRecordCount': 5, 'Records': [
                {'ErrorCode': 0}, {'ErrorCode': 1}, {'ErrorCode': 2},
                {'ErrorCode': 3}, {'ErrorCode': 4}]}] * 5

        with pytest.raises(KinesisClientError):
            test_instance._send_kinesis_format_records(
                _TEST_KINESIS_RECORDS, 1)

        test_instance.kinesis_client.put_records.assert_has_calls([
            mocker.call(Records=_TEST_KINESIS_RECORDS,
                        StreamARN='test_stream_arn')] * 5)
