import os
import json
import pytest
from requests_oauthlib import OAuth2Session

from nypl_py_utils import PlatformApiClient
# from requests.exceptions import ConnectTimeout

_TOKEN_RESPONSE = {
    'access_token': 'super-secret-token',
    'expires_in': 3600,
    'token_type': 'Bearer',
    'scope': ['offline_access', 'openid', 'login:staff', 'admin'],
    'id_token': 'super-secret-token',
    'expires_at': 1677599823.3180869
}

BASE_URL = 'https://example.com/api/v0.1'


class TestPlatformApiClient:

    @pytest.fixture
    def test_instance(self, requests_mock):
        token_url = 'https://oauth.example.com/oauth/token'
        requests_mock.post(token_url, text=json.dumps(_TOKEN_RESPONSE))

        return PlatformApiClient(base_url=BASE_URL,
                                 token_url=token_url,
                                 client_id='clientid',
                                 client_secret='clientsecret'
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

        client = PlatformApiClient()
        assert client.client_id == 'env client id'
        assert client.client_secret == 'env client secret'
        assert client.token_url == 'env token url'
        assert client.base_url == 'env base url'

        for key, value in env.items():
            os.environ[key] = ''

    def test_generate_access_token(self, test_instance):
        test_instance._generate_access_token()
        assert test_instance.token['access_token']\
            == _TOKEN_RESPONSE['access_token']

    def test_create_oauth_client(self, test_instance):
        test_instance._create_oauth_client()
        assert type(test_instance.oauth_client) is OAuth2Session

    def test_do_http_method(self, requests_mock, test_instance):
        requests_mock.get(f'{BASE_URL}/foo', json={'foo': 'bar'})
        resp = test_instance._do_http_method('GET', 'foo')
        assert resp == {'foo': 'bar'}

    def test_token_expiration(self, requests_mock, test_instance):
        api_get_mock = requests_mock.get(f'{BASE_URL}/foo',
                                         json={'foo': 'bar'})

        # Perform first request to auto-authenticate:
        resp = test_instance._do_http_method('GET', 'foo')
        assert api_get_mock.request_history[0]._request\
            .headers['Authorization'] == 'Bearer super-secret-token'

        # Emulate token expiration:
        test_instance.token['expires_at'] = 0

        token_post_mock = requests_mock.post(
            test_instance.token_url,
            text=json.dumps(_TOKEN_RESPONSE)
        )

        # Perform second request, which should detect token expiration and
        # re-authenticate:
        resp = test_instance._do_http_method('GET', 'foo')

        assert token_post_mock.called is True
        assert api_get_mock.request_history[1]._request\
            .headers['Authorization'] == 'Bearer super-secret-token'
        assert resp == {'foo': 'bar'}
