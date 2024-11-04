import base64
import hashlib
import hmac
import requests

from datetime import datetime, timedelta
from nypl_py_utils.functions.log_helper import create_log
from requests.adapters import HTTPAdapter, Retry

_API_URL = "https://partner.yourcloudlibrary.com/cirrus/library"
_VERSION = "3.0.2"


class CloudLibraryClient:
    """Client for interacting with CloudLibrary API v3.0.2"""

    def __init__(self, library_id, account_id, account_key):
        self.logger = create_log("cloudlibrary_client")
        self.library_id = library_id
        self.account_id = account_id
        self.account_key = account_key
        self.base_url = f"{_API_URL}/{self.library_id}"
        self.setup_session()

    def setup_session(self):
        """Authenticate and set up HTTP session"""
        retry_policy = Retry(total=3, backoff_factor=45,
                             status_forcelist=[500, 502, 503, 504],
                             allowed_methods=frozenset(["GET"]))
        self.session = requests.Session()
        self.session.mount("https://",
                           HTTPAdapter(max_retries=retry_policy))

    def get_library_events(self, start_date: str, end_date: str) -> requests.Response:
        """
        Retrieves all the events related to library-owned items within the 
        optional timeframe. Pulls yesterday's events by default.
        """
        yesterday = datetime.now() - timedelta(1)
        yesterday_formatted = datetime.strftime(yesterday, "%Y-%m-%d")
        start_date = yesterday_formatted if start_date is None else start_date
        end_date = yesterday_formatted if end_date is None else end_date

        path = f"data/cloudevents?startdate{start_date}&enddate={end_date}"
        response = self.request(path, "GET")
        return response

    def create_request_body_with_filter(self, request_type: str, item_id: str, patron_id: str) -> str:
        """
        Helper function to generate request body when performing item 
        and/or patron-specific functions (ex. checking out a title). 
        """
        request_template = "<%(request_type)s><ItemId>%(item_id)s</ItemId><PatronId>%(patron_id)s</PatronId></%(request_type)s>"
        return request_template % {
            "request_type": request_type,
            "item_id": item_id,
            "patron_id": patron_id,
        }

    def request(self, path, body=None, method_type="GET") -> requests.Response:
        headers = self._build_headers(method_type, path)
        url = f"{self.base_url}/{path}"
        method_type = method_type.upper()

        try:
            if method_type == "GET":
                response = self.session.get(url=url,
                                            data=body,
                                            headers=headers,
                                            timeout=60)
            elif method_type == "PUT":
                response = self.session.put(url=url,
                                            data=body,
                                            headers=headers,
                                            timeout=60)
            else:
                response = self.session.post(url=url,
                                             data=body,
                                             headers=headers,
                                             timeout=60)
            response.raise_for_status()
        except Exception as e:
            error_message = f"Failed to retrieve response from {url}: {e}"
            self.logger.error(error_message)
            raise CloudLibraryClientError(error_message)

        return response

    def _build_headers(self, method_type: str, path: str) -> dict:
        time, authorization = self._build_authorization(method_type, path)
        headers = {
            "3mcl-Datetime": time,
            "3mcl-Authorization": authorization,
            "3mcl-Version": _VERSION,
        }

        if method_type == "GET":
            headers["Accept"] = "application/xml"
        else:
            headers["Content-Type"] = "application/xml"

        return headers

    def _build_authorization(self, method_type: str, path: str) -> tuple[str, str]:
        now = datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
        message = "\n".join([now, method_type, path])
        digest = hmac.new(
            self.account_key.encode("utf-8"),
            msg=message.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()
        signature = base64.standard_b64decode(digest).decode()

        return now, f"3MCLAUTH {self.account_id}:{signature}"


class CloudLibraryClientError(Exception):
    def __init__(self, message=None):
        self.message = message
