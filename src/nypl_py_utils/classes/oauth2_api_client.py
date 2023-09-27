import os
from time import sleep
from requests.models import Response
from oauthlib.oauth2 import BackendApplicationClient, TokenExpiredError
from requests_oauthlib import OAuth2Session
from nypl_py_utils.functions.log_helper import create_log


class Oauth2ApiClient:
    """
    Client for interacting with an Oauth2 authenticated API such as NYPL's
    Platform API endpoints
    """

    def __init__(self, client_id=None, client_secret=None, base_url=None,
                 token_url=None, with_retries=False):
        self.client_id = client_id \
            or os.environ.get('NYPL_API_CLIENT_ID', None)
        self.client_secret = client_secret \
            or os.environ.get('NYPL_API_CLIENT_SECRET', None)
        self.token_url = token_url \
            or os.environ.get('NYPL_API_TOKEN_URL', None)
        self.base_url = base_url \
            or os.environ.get('NYPL_API_BASE_URL', None)

        self.oauth_client = None

        self.logger = create_log('oauth2_api_client')

        self.with_retries = with_retries

    def get(self, request_path, **kwargs):
        """
        Issue an HTTP GET on the given request_path
        """
        resp = self._do_http_method('GET', request_path, **kwargs)
        if resp.json() is None and self.with_retries is True:
            retries = \
                kwargs.get('retries', 0) + 1
            if retries < 3:
                self.logger.warning(
                    f'Retrying get request due to empty response from\
                         Oauth2 Client. Retry #{retries}')
                sleep(pow(2, retries - 1))
                kwargs['retries'] = retries
                resp = self.get(request_path, **kwargs)
            else:
                resp = Response()
                resp.message = 'Oauth2 Client: Request failed after 3 \
                        empty responses received from Oauth2 Client'
                resp.status_code = 500
        return resp

    def post(self, request_path, json, **kwargs):
        """
        Issue an HTTP POST on the given request_path with given JSON body
        """
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
        if not self.oauth_client:
            self._create_oauth_client()

        url = f'{self.base_url}/{request_path}'
        self.logger.debug(f'{method} {url}')

        try:
            # Build kwargs cleaned of local variables:
            kwargs_cleaned = {k: kwargs[k] for k in kwargs
                              if not k.startswith('_do_http_method_')}
            resp = self.oauth_client.request(method, url, **kwargs_cleaned)
            resp.raise_for_status()
            return resp
        except TokenExpiredError:
            self.logger.debug('TokenExpiredError encountered')

            # Raise error after 3 successive token refreshes
            kwargs['_do_http_method_token_refreshes'] = \
                kwargs.get('_do_http_method_token_refreshes', 0) + 1
            if kwargs['_do_http_method_token_refreshes'] > 3:
                raise Oauth2ApiClientError('Exhausted token refreshes') \
                    from None

            self._generate_access_token()
            return self._do_http_method(method, request_path, **kwargs).json()

    def _create_oauth_client(self):
        """
        Creates an authenticated a OAuth2Session instance for later requests
        """
        client = BackendApplicationClient(client_id=self.client_id)
        self.oauth_client = OAuth2Session(client=client)
        self._generate_access_token()

    def _generate_access_token(self):
        """
        Fetch and store a fresh token
        """
        self.logger.debug(f'Refreshing token via @{self.token_url}')
        self.oauth_client.fetch_token(
            token_url=self.token_url,
            client_id=self.client_id,
            client_secret=self.client_secret
        )


class Oauth2ApiClientError(Exception):
    def __init__(self, message=None):
        self.message = message
