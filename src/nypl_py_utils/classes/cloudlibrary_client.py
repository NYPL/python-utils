import base64
import hashlib
import hmac
import requests

from datetime import datetime, timezone
from nypl_py_utils.functions.log_helper import create_log
from requests.adapters import HTTPAdapter, Retry

_API_URL = "https://partner.yourcloudlibrary.com"
_VERSION = "3.0.2"


class CloudLibraryClient:
    """Client for interacting with CloudLibrary API v3.0.2"""

    def __init__(self, library_id, account_id, account_key):
        self.logger = create_log("cloudlibrary_client")
        self.library_id = library_id
        self.account_id = account_id
        self.account_key = account_key

        # authenticate & set up HTTP session
        retry_policy = Retry(total=3, backoff_factor=45,
                             status_forcelist=[500, 502, 503, 504],
                             allowed_methods=frozenset(["GET"]))
        self.session = requests.Session()
        self.session.mount("https://",
                           HTTPAdapter(max_retries=retry_policy))

    def get_library_events(self, start_date=None,
                           end_date=None) -> requests.Response:
        """
        Retrieves all the events related to library-owned items within the
        optional timeframe. Pulls past 24 hours of events by default.

        start_date and end_date are optional parameters, and must be
        formatted either YYYY-MM-DD, YYYY-MM-DD:SS, or YYYY-MM-DDTHH:MM:SS.fff
        """
        path = "data/cloudevents"
        if None not in (start_date, end_date):
            if (self._parse_event_date(start_date) >
                    self._parse_event_date(end_date)):
                error_message = (f"Start date {start_date} greater than end "
                                 f"date {end_date}, cannot retrieve library "
                                 f"events")
                self.logger.error(error_message)
                raise CloudLibraryClientError(error_message)

            path += f"?startdate={start_date}&enddate={end_date}"
            self.logger.info(f"Fetching all library events in "
                             f"time frame {start_date} to {end_date}...")
        else:
            self.logger.info("Fetching all library events "
                             "from the past day...")

        response = self.request(path=path, method_type="GET")
        return response

    def create_request_body(self, request_type,
                            item_id, patron_id) -> str:
        """
        Helper function to generate request body when performing item
        and/or patron-specific functions (ex. checking out a title).
        """
        request_template = "<%(request_type)s><ItemId>%(item_id)s</ItemId><PatronId>%(patron_id)s</PatronId></%(request_type)s>"  # noqa
        return request_template % {
            "request_type": request_type,
            "item_id": item_id,
            "patron_id": patron_id,
        }

    def request(self, path, method_type="GET",
                body=None) -> requests.Response:
        """
        Use this method to call specific paths in the cloudLibrary API.
        This method is necessary for building headers/authorization.
        Example usage of this method is in the get_library_events function.

        Returns Response object by default -- you will need to parse this
        object to retrieve response text, status codes, etc.
        """
        extended_path = f"/cirrus/library/{self.library_id}/{path}"
        headers = self._build_headers(method_type, extended_path)
        url = f"{_API_URL}{extended_path}"
        method_type = method_type.upper()

        try:
            if method_type == "PUT":
                response = self.session.put(url=url,
                                            data=body,
                                            headers=headers,
                                            timeout=60)
            elif method_type == "POST":
                response = self.session.post(url=url,
                                             data=body,
                                             headers=headers,
                                             timeout=60)
            else:
                response = self.session.get(url=url,
                                            data=body,
                                            headers=headers,
                                            timeout=60)
            response.raise_for_status()
        except Exception as e:
            error_message = (f"Failed to retrieve response from {url}: "
                             f"{repr(e)}")
            self.logger.error(error_message)
            raise CloudLibraryClientError(error_message)

        return response

    def _parse_event_date(self, event_date) -> datetime:
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
            try:
                return datetime.strptime(event_date, fmt)
            except ValueError:
                pass
        error_message = (f"Invalid date format found: {event_date}")
        self.logger.error(error_message)
        raise CloudLibraryClientError(error_message)

    def _build_headers(self, method_type, path) -> dict:
        time, authorization = self._build_authorization(
            method_type, path)
        headers = {
            "3mcl-Datetime": time,
            "3mcl-Authorization": authorization,
            "3mcl-APIVersion": _VERSION,
        }

        if method_type == "GET":
            headers["Accept"] = "application/xml"
        else:
            headers["Content-Type"] = "application/xml"

        return headers

    def _build_authorization(self, method_type,
                             path) -> tuple[str, str]:
        now = datetime.now(timezone.utc).strftime(
            "%a, %d %b %Y %H:%M:%S GMT")
        message = "\n".join([now, method_type, path])
        digest = hmac.new(
            self.account_key.encode("utf-8"),
            msg=message.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()
        signature = base64.standard_b64encode(digest).decode()

        return now, f"3MCLAUTH {self.account_id}:{signature}"


class CloudLibraryClientError(Exception):
    def __init__(self, message=None):
        self.message = message
