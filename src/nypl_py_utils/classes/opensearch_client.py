import boto3
import os

from botocore.exceptions import ClientError
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
from nypl_py_utils.functions.log_helper import create_log


class OpenSearchClient:
    """
    Client for interacting with an AWS OpenSearch Service domain.

    Takes as input the OpenSearch domain endpoint (without the https:// scheme)
    and an optional AWS region. Authentication is performed via AWS IAM using
    SigV4 request signing.
    """

    def __init__(self, host, region=None):
        self.logger = create_log('opensearch_client')
        self.host = host
        self.region = region or os.environ.get('AWS_REGION', 'us-east-1')

        try:
            credentials = boto3.Session().get_credentials()
            auth = AWSV4SignerAuth(credentials, self.region, 'es')
            self.client = OpenSearch(
                hosts=[{'host': self.host, 'port': 443}],
                http_auth=auth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                pool_maxsize=10
            )
        except ClientError as e:
            self.logger.error(
                'Could not create OpenSearch client: {err}'.format(err=e))
            raise OpenSearchClientError(
                'Could not create OpenSearch client: {err}'.format(err=e)
            ) from None

    def create_index(self, index, body=None):
        """
        Creates an OpenSearch index with optional mappings and settings.

        Parameters
        ----------
        index: str
            The name of the index to create
        body: dict, optional
            The index settings and/or mappings
        """
        self.logger.info('Creating OpenSearch index {}'.format(index))
        try:
            return self.client.indices.create(index=index, body=body)
        except Exception as e:
            self.logger.error(
                'Error creating OpenSearch index {name}: {error}'.format(
                    name=index, error=e))
            raise OpenSearchClientError(
                'Error creating OpenSearch index {name}: {error}'.format(
                    name=index, error=e)) from None

    def index_document(self, index, document, document_id=None):
        """
        Indexes a document in the given OpenSearch index.

        Parameters
        ----------
        index: str
            The name of the index
        document: dict
            The document to index
        document_id: str, optional
            The ID to assign to the document. If not provided, OpenSearch
            will auto-generate one.
        """
        self.logger.info(
            'Indexing document in OpenSearch index {}'.format(index))
        try:
            return self.client.index(
                index=index, body=document, id=document_id)
        except Exception as e:
            self.logger.error(
                'Error indexing document in OpenSearch index {name}: '
                '{error}'.format(name=index, error=e))
            raise OpenSearchClientError(
                'Error indexing document in OpenSearch index {name}: '
                '{error}'.format(name=index, error=e)) from None

    def delete_document(self, index, document_id):
        """
        Deletes a document from the given OpenSearch index by ID.

        Parameters
        ----------
        index: str
            The name of the index
        document_id: str
            The ID of the document to delete
        """
        self.logger.info(
            'Deleting document {id} from OpenSearch index {index}'.format(
                id=document_id, index=index))
        try:
            return self.client.delete(index=index, id=document_id)
        except Exception as e:
            self.logger.error(
                'Error deleting document {id} from OpenSearch index '
                '{name}: {error}'.format(
                    id=document_id, name=index, error=e))
            raise OpenSearchClientError(
                'Error deleting document {id} from OpenSearch index '
                '{name}: {error}'.format(
                    id=document_id, name=index, error=e)) from None

    def search(self, index, query):
        """
        Executes a search query against the given OpenSearch index.

        Parameters
        ----------
        index: str
            The name of the index to search
        query: dict
            The OpenSearch query body

        Returns
        -------
        dict
            The OpenSearch response containing hits and metadata
        """
        self.logger.info('Searching OpenSearch index {}'.format(index))
        self.logger.debug('Executing query {}'.format(query))
        try:
            return self.client.search(index=index, body=query)
        except Exception as e:
            self.logger.error(
                'Error searching OpenSearch index {name}: {error}'.format(
                    name=index, error=e))
            raise OpenSearchClientError(
                'Error searching OpenSearch index {name}: {error}'.format(
                    name=index, error=e)) from None

    def close_connection(self):
        """Closes the OpenSearch connection"""
        self.logger.debug(
            'Closing OpenSearch connection to {}'.format(self.host))
        self.client.close()


class OpenSearchClientError(Exception):
    def __init__(self, message=None):
        self.message = message
