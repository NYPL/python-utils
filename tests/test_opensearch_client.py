import pytest

from nypl_py_utils.classes.opensearch_client import (
    OpenSearchClient, OpenSearchClientError)

_TEST_HOST = 'test-domain.us-east-1.es.amazonaws.com'
_TEST_INDEX = 'test-index'
_TEST_DOC_ID = 'test-doc-id'
_TEST_DOCUMENT = {'title': 'Test Document', 'body': 'Test body content'}
_TEST_QUERY = {'query': {'match': {'title': 'test'}}}
_TEST_RESPONSE = {
    'hits': {
        'total': {'value': 1, 'relation': 'eq'},
        'hits': [{'_index': _TEST_INDEX, '_id': _TEST_DOC_ID,
                  '_source': _TEST_DOCUMENT}]
    }
}


class TestOpenSearchClient:

    @pytest.fixture
    def test_instance(self, mocker):
        mocker.patch('boto3.Session')
        mocker.patch('nypl_py_utils.classes.opensearch_client.AWSV4SignerAuth')
        mocker.patch('nypl_py_utils.classes.opensearch_client.OpenSearch')
        return OpenSearchClient(_TEST_HOST)

    def test_create_index(self, test_instance):
        test_instance.create_index(_TEST_INDEX)
        test_instance.client.indices.create.assert_called_once_with(
            index=_TEST_INDEX, body=None)

    def test_create_index_with_body(self, test_instance):
        body = {'mappings': {'properties': {'title': {'type': 'text'}}}}
        test_instance.create_index(_TEST_INDEX, body=body)
        test_instance.client.indices.create.assert_called_once_with(
            index=_TEST_INDEX, body=body)

    def test_create_index_error(self, test_instance):
        test_instance.client.indices.create.side_effect = Exception('error')
        with pytest.raises(OpenSearchClientError):
            test_instance.create_index(_TEST_INDEX)

    def test_index_document(self, test_instance):
        test_instance.index_document(_TEST_INDEX, _TEST_DOCUMENT, _TEST_DOC_ID)
        test_instance.client.index.assert_called_once_with(
            index=_TEST_INDEX, body=_TEST_DOCUMENT, id=_TEST_DOC_ID)

    def test_index_document_without_id(self, test_instance):
        test_instance.index_document(_TEST_INDEX, _TEST_DOCUMENT)
        test_instance.client.index.assert_called_once_with(
            index=_TEST_INDEX, body=_TEST_DOCUMENT, id=None)

    def test_index_document_error(self, test_instance):
        test_instance.client.index.side_effect = Exception('error')
        with pytest.raises(OpenSearchClientError):
            test_instance.index_document(_TEST_INDEX, _TEST_DOCUMENT)

    def test_delete_document(self, test_instance):
        test_instance.delete_document(_TEST_INDEX, _TEST_DOC_ID)
        test_instance.client.delete.assert_called_once_with(
            index=_TEST_INDEX, id=_TEST_DOC_ID)

    def test_delete_document_error(self, test_instance):
        test_instance.client.delete.side_effect = Exception('error')
        with pytest.raises(OpenSearchClientError):
            test_instance.delete_document(_TEST_INDEX, _TEST_DOC_ID)

    def test_search(self, test_instance):
        test_instance.client.search.return_value = _TEST_RESPONSE
        result = test_instance.search(_TEST_INDEX, _TEST_QUERY)
        test_instance.client.search.assert_called_once_with(
            index=_TEST_INDEX, body=_TEST_QUERY)
        assert result == _TEST_RESPONSE

    def test_search_error(self, test_instance):
        test_instance.client.search.side_effect = Exception('error')
        with pytest.raises(OpenSearchClientError):
            test_instance.search(_TEST_INDEX, _TEST_QUERY)

    def test_close_connection(self, test_instance):
        test_instance.close_connection()
        test_instance.client.close.assert_called_once()
