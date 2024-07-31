import json
import pytest

from nypl_py_utils.classes.avro_client import (
    AvroClientError, AvroDecoder, AvroEncoder)
from requests.exceptions import ConnectTimeout

_TEST_SCHEMA = {'data': {'schema': json.dumps({
    'name': 'TestSchema',
    'type': 'record',
    'fields': [
        {
            'name': 'patron_id',
            'type': 'int'
        },
        {
            'name': 'library_branch',
            'type': ['null', 'string']
        }
    ]
})}}


class TestAvroClient:
    @pytest.fixture
    def test_avro_encoder_instance(self, requests_mock):
        requests_mock.get(
            "https://test_schema_url", text=json.dumps(_TEST_SCHEMA))
        return AvroEncoder("https://test_schema_url")

    @pytest.fixture
    def test_avro_decoder_instance(self, requests_mock):
        requests_mock.get(
            "https://test_schema_url", text=json.dumps(_TEST_SCHEMA))
        return AvroDecoder("https://test_schema_url")

    def test_get_json_schema_success(self, test_avro_encoder_instance,
                                     test_avro_decoder_instance):
        assert test_avro_encoder_instance.schema == _TEST_SCHEMA["data"][
            "schema"]
        assert test_avro_decoder_instance.schema == _TEST_SCHEMA["data"][
            "schema"]

    def test_get_json_schema_error(self, requests_mock):
        requests_mock.get("https://test_schema_url", exc=ConnectTimeout)
        with pytest.raises(AvroClientError):
            AvroEncoder("https://test_schema_url")

    def test_bad_json_error(self, requests_mock):
        requests_mock.get(
            'https://test_schema_url', text='bad json')
        with pytest.raises(AvroClientError):
            AvroEncoder('https://test_schema_url')

    def test_missing_key_error(self, requests_mock):
        requests_mock.get(
            'https://test_schema_url', text=json.dumps({'field': 'value'}))
        with pytest.raises(AvroClientError):
            AvroEncoder('https://test_schema_url')

    def test_encode_record(self, test_avro_encoder_instance,
                           test_avro_decoder_instance):
        TEST_RECORD = {'patron_id': 123, 'library_branch': 'aa'}
        encoded_record = test_avro_encoder_instance.encode_record(TEST_RECORD)
        assert type(encoded_record) is bytes
        assert test_avro_decoder_instance.decode_record(
            encoded_record) == TEST_RECORD

    def test_encode_record_error(self, test_avro_encoder_instance):
        TEST_RECORD = {'patron_id': 123, 'bad_field': 'bad'}
        with pytest.raises(AvroClientError):
            test_avro_encoder_instance.encode_record(TEST_RECORD)

    def test_encode_batch(self, test_avro_encoder_instance,
                          test_avro_decoder_instance):
        TEST_BATCH = [
            {'patron_id': 123, 'library_branch': 'aa'},
            {'patron_id': 456, 'library_branch': None},
            {'patron_id': 789, 'library_branch': 'bb'}]
        encoded_records = test_avro_encoder_instance.encode_batch(TEST_BATCH)
        assert len(encoded_records) == len(TEST_BATCH)
        for i in range(3):
            assert type(encoded_records[i]) is bytes
            assert test_avro_decoder_instance.decode_record(
                encoded_records[i]) == TEST_BATCH[i]

    def test_encode_batch_error(self, test_avro_encoder_instance):
        BAD_BATCH = [
            {'patron_id': 123, 'library_branch': 'aa'},
            {'patron_id': 456, 'bad_field': 'bad'}]
        with pytest.raises(AvroClientError):
            test_avro_encoder_instance.encode_batch(BAD_BATCH)

    def test_decode_record(self, test_avro_decoder_instance):
        TEST_DECODED_RECORD = {"patron_id": 123, "library_branch": "aa"}
        TEST_ENCODED_RECORD = b'\xf6\x01\x02\x04aa'
        assert test_avro_decoder_instance.decode_record(
            TEST_ENCODED_RECORD) == TEST_DECODED_RECORD

    def test_decode_record_error(self, test_avro_decoder_instance):
        TEST_ENCODED_RECORD = b'bad-encoding'
        with pytest.raises(AvroClientError):
            test_avro_decoder_instance.decode_record(TEST_ENCODED_RECORD)

    def test_decode_batch(self, test_avro_decoder_instance):
        TEST_ENCODED_BATCH = [
            b'\xf6\x01\x02\x04aa',
            b'\x90\x07\x00',
            b'\xaa\x0c\x02\x04bb']
        TEST_DECODED_BATCH = [
            {'patron_id': 123, 'library_branch': 'aa'},
            {'patron_id': 456, 'library_branch': None},
            {'patron_id': 789, 'library_branch': 'bb'}]
        assert test_avro_decoder_instance.decode_batch(
            TEST_ENCODED_BATCH) == TEST_DECODED_BATCH

    def test_decode_batch_error(self, test_avro_decoder_instance):
        BAD_BATCH = [
            b'\xf6\x01\x02\x04aa',
            b'bad-encoding']
        with pytest.raises(AvroClientError):
            test_avro_decoder_instance.decode_batch(BAD_BATCH)
