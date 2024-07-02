import os
import time
import json
import pytest
from requests_oauthlib import OAuth2Session
from requests import HTTPError, JSONDecodeError, Response

from nypl_py_utils.classes.oauth2_api_client import (Oauth2ApiClient,
                                                     Oauth2ApiClientError)

_TOKEN_RESPONSE = {
    'access_token': 'super-secret-token',
    'expires_in': 1,
    'token_type': 'Bearer',
    'scope': ['offline_access', 'openid', 'login:staff', 'admin'],
    'id_token': 'super-secret-token'
}

BASE_URL = 'https://example.com/api/v0.1'
TOKEN_URL = 'https://oauth.example.com/oauth/token'


class MockEmptyResponse:
    def __init__(self, empty, status_code=None):
        self.status_code = status_code
        self.empty = empty
        self.text = "error text"

    def json(self):
        if self.empty:
            raise JSONDecodeError
        else:
            return 'success'


class TestOauth2ApiClient:

    @pytest.fixture
    def token_server_post(self, requests_mock):
        token_url = TOKEN_URL
        token_response = dict(_TOKEN_RESPONSE)
        return requests_mock.post(token_url, text=json.dumps(token_response))

    @pytest.fixture
    def test_instance(self, requests_mock):
        return Oauth2ApiClient(base_url=BASE_URL,
                               token_url=TOKEN_URL,
                               client_id='clientid',
                               client_secret='clientsecret'
                               )

    @pytest.fixture
    def test_instance_with_retries(self, requests_mock):
        return Oauth2ApiClient(base_url=BASE_URL,
                               token_url=TOKEN_URL,
                               client_id='clientid',
                               client_secret='clientsecret',
                               with_retries=True
                               )

    def test_uses_env_vars(self):
        env = {
            'NYPL_API_CLIENT_ID': 'env client id',
            'NYPL_API_CLIENT_SECRET': 'env client secret',
            'NYPL_API_TOKEN_URL': 'env token url',
            'NYPL_API_BASE_URL': 'env base url'
        }
        for key, value in env.items():
            os.environ[key] = value

        client = Oauth2ApiClient()
        assert client.client_id == 'env client id'
        assert client.client_secret == 'env client secret'
        assert client.token_url == 'env token url'
        assert client.base_url == 'env base url'

        for key, value in env.items():
            os.environ[key] = ''

    def test_generate_access_token(self, test_instance, token_server_post):
        test_instance._create_oauth_client()
        test_instance._generate_access_token()
        assert test_instance.oauth_client.token['access_token']\
            == _TOKEN_RESPONSE['access_token']

    def test_create_oauth_client(self, token_server_post, test_instance):
        test_instance._create_oauth_client()
        assert type(test_instance.oauth_client) is OAuth2Session

    def test_do_http_method(self, requests_mock, token_server_post,
                            test_instance):
        requests_mock.get(f'{BASE_URL}/foo', json={'foo': 'bar'})

        requests_mock.get(f'{BASE_URL}/foo', json={'foo': 'bar'})
        resp = test_instance._do_http_method('GET', 'foo')
        assert resp.status_code == 200
        assert resp.json() == {'foo': 'bar'}

    def test_token_expiration(self, requests_mock, test_instance,
                              token_server_post, mocker):
        api_get_mock = requests_mock.get(f'{BASE_URL}/foo',
                                         json={'foo': 'bar'})

        # Perform first request:
        test_instance._do_http_method('GET', 'foo')
        # Expect this first call triggered a single token server call:
        assert len(token_server_post.request_history) == 1
        # And the GET request used the supplied Bearer token:
        assert api_get_mock.request_history[0]._request\
            .headers['Authorization'] == 'Bearer super-secret-token'

        # The token obtained above expires in 1s, so wait out expiration:
        time.sleep(1.1)

        # Register new token response:
        second_token_response = dict(_TOKEN_RESPONSE)
        second_token_response['id_token'] = 'super-secret-second-token'
        second_token_response['access_token'] = 'super-secret-second-token'
        second_token_server_post = requests_mock\
            .post(TOKEN_URL, text=json.dumps(second_token_response))

        # Perform second request:
        response = test_instance._do_http_method('GET', 'foo')
        # Ensure we still return a plain requests Response object
        assert isinstance(response, Response)
        assert response.json() == {"foo": "bar"}
        # Expect a call on the second token server:
        assert len(second_token_server_post.request_history) == 1
        # Expect the second GET request to carry the new Bearer token:
        assert api_get_mock.request_history[1]._request\
            .headers['Authorization'] == 'Bearer super-secret-second-token'

    def test_error_status_raises_error(self, requests_mock, test_instance,
                                       token_server_post):
        requests_mock.get(f'{BASE_URL}/foo', status_code=400)

        with pytest.raises(HTTPError):
            test_instance._do_http_method('GET', 'foo')

    def test_token_refresh_failure_raises_error(
            self, requests_mock, test_instance, token_server_post):
        """
        Failure to fetch a token can raise a number of errors including:
         - requests.exceptions.HTTPError for invalid access_token
         - oauthlib.oauth2.rfc6749.errors.InvalidClientError for invalid
           credentials
         - oauthlib.oauth2.rfc6749.errors.MissingTokenError for failure to
           fetch a token
        One error that can arise from this client itself is failure to fetch
        a new valid token in response to token expiration. This test asserts
        that the client will not allow more than successive 3 retries.
        """
        requests_mock.get(f'{BASE_URL}/foo', json={'foo': 'bar'})

        token_response = dict(_TOKEN_RESPONSE)
        token_response['expires_in'] = 0
        token_server_post = requests_mock\
            .post(TOKEN_URL, text=json.dumps(token_response))

        with pytest.raises(Oauth2ApiClientError):
            test_instance._do_http_method('GET', 'foo')
        # Expect 1 initial token fetch, plus 3 retries:
        assert len(token_server_post.request_history) == 4

    def test_bad_response_no_retries(self, requests_mock, test_instance,
                                     mocker):
        mocker.patch.object(test_instance, '_do_http_method',
                            return_value=MockEmptyResponse(empty=True))
        get_spy = mocker.spy(test_instance, 'get')
        resp = test_instance.get('spaghetti')
        assert get_spy.call_count == 1
        assert resp.status_code == 500
        assert resp.message == 'Oauth2 Client: Bad response from OauthClient'

    def test_http_retry_fail(self, requests_mock, test_instance_with_retries,
                             mocker):
        mocker.patch.object(test_instance_with_retries, '_do_http_method',
                            return_value=MockEmptyResponse(empty=True))
        get_spy = mocker.spy(test_instance_with_retries, 'get')
        resp = test_instance_with_retries.get('spaghetti')
        assert get_spy.call_count == 3
        assert resp.status_code == 500
        assert resp.message == 'Oauth2 Client: Request failed after 3 \
                            empty responses received from Oauth2 Client'

    def test_http_retry_success(self, requests_mock,
                                test_instance_with_retries, mocker):
        mocker.patch.object(test_instance_with_retries, '_do_http_method',
                            side_effect=[MockEmptyResponse(empty=True),
                                         MockEmptyResponse(empty=False,
                                                           status_code=200)])
        get_spy = mocker.spy(test_instance_with_retries, 'get')
        resp = test_instance_with_retries.get('spaghetti')
        assert get_spy.call_count == 2
        assert resp.json() == 'success'
