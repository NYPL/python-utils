import json
import pandas as pd
import pytest

from nypl_py_utils import AvroEncoder, AvroEncoderError

_MOCK_SCHEMA = {'data': {'schema': json.dumps({
    'name': 'MockSchema',
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


class TestAvroEncoder:

    @pytest.fixture
    def test_instance(self, requests_mock):
        requests_mock.get(
            'https://test_schema_url', text=json.dumps(_MOCK_SCHEMA))
        return AvroEncoder('https://test_schema_url')

    def test_get_json_schema(self, test_instance):
        assert test_instance.schema == _MOCK_SCHEMA['data']['schema']

    def test_encode_batch_success(self, test_instance):
        TEST_BATCH = pd.DataFrame(
            {'patron_id': [123, 456, 789],
             'library_branch': ['aa', None, 'bb']})
        encoded_records = test_instance.encode_batch(TEST_BATCH)
        assert len(encoded_records) == len(TEST_BATCH)
        for i in range(3):
            assert type(encoded_records[i]) is bytes
            assert test_instance.decode_record(
                encoded_records[i]) == TEST_BATCH.loc[i].to_dict()

    def test_encode_batch_error(self, test_instance):
        BAD_BATCH = pd.DataFrame(
            {'patron_id': [123, 456], 'bad_field': ['bad', 'field']})
        with pytest.raises(AvroEncoderError):
            test_instance.encode_batch(BAD_BATCH)
