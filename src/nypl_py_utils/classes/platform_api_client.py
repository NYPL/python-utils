import os
from oauthlib.oauth2 import BackendApplicationClient, TokenExpiredError
from requests_oauthlib import OAuth2Session
from nypl_py_utils.functions.log_helper import create_log


class PlatformApiClient:
    """
    Client for interacting with NYPL Platform API endpoints
    """

    def __init__(self, client_id=None, client_secret=None, base_url=None,
                 token_url=None):
        self.client_id = client_id \
            or os.environ.get('NYPL_API_CLIENT_ID', None)
        self.client_secret = client_secret \
            or os.environ.get('NYPL_API_CLIENT_SECRET', None)
        self.token_url = token_url \
            or os.environ.get('NYPL_API_TOKEN_URL', None)
        self.base_url = base_url \
            or os.environ.get('NYPL_API_BASE_URL', None)

        self.client = None
        self.token = None

        self.logger = create_log('platform_api_client')

    def get(self, request_path, **kwargs):
        """
        Issue an HTTP GET on the given request_path
        """
        return self._do_http_method('GET', request_path, **kwargs)

    def post(self, request_path, json, **kwargs):
        """
        Issue an HTTP POST on the given request_path with given JSON body
        """
        return self._do_http_method('GET', request_path, **kwargs)
        kwargs['json'] = json
        return self._do_http_method('POST', request_path, **kwargs)

    def patch(self, request_path, json, **kwargs):
        """
        Issue an HTTP PATCH on the given request_path with given JSON body
        """
        kwargs['json'] = json
        return self._do_http_method('PATCH', request_path, **kwargs)

    def delete(self, request_path, **kwargs):
        """
        Issue an HTTP DELETE on the given request_path
        """
        return self._do_http_method('DELETE', request_path, **kwargs)

    def _do_http_method(self, method, request_path, **kwargs):
        """
        Issue an HTTP method call on on the given request_path
        """
        if not self.client:
            self._create_oauth_client()

        url = f'{self.base_url}/{request_path}'
        self.logger.debug(f'{method} {url}')

        try:
            return self.oauth_client.request(method, url, **kwargs).json()
        except TokenExpiredError as e:
            print(f'TokenExpiredError encountered: {e}')
            self._generate_access_token()

            return self._do_http_method(method, request_path, **kwargs)
        except TimeoutError as e:
            print(f'TimeoutError encountered: {e}')
            return {}

    def _create_oauth_client(self):
        """
        Creates an authenticated a OAuth2Session instance for later requests
        """
        self._generate_access_token()
        self.oauth_client = OAuth2Session(self.client_id, token=self.token)

    def _generate_access_token(self):
        """
        Fetch and store a fresh token
        """
        client = BackendApplicationClient(client_id=self.client_id)
        oauth = OAuth2Session(client=client)
        self.logger.debug(f'Refreshing token via @{self.token_url}')
        self.token = oauth.fetch_token(
            token_url=self.token_url,
            client_id=self.client_id,
            client_secret=self.client_secret
        )
