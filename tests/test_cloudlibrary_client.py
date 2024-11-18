import pytest

from freezegun import freeze_time
from requests import ConnectTimeout
from nypl_py_utils.classes.cloudlibrary_client import (
    CloudLibraryClient, CloudLibraryClientError)

_API_URL = "https://partner.yourcloudlibrary.com/cirrus/library/"

# catch-all API response since we're not testing actual data
_TEST_LIBRARY_EVENTS_RESPONSE = """<LibraryEventBatch
xmlns:xsd="http://www.w3.org/2001/XMLSchema"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<PublishId>4302fcca-ef99-49bf-bd29-d673e990f765</PublishId>
<PublishDateTimeInUTC>2024-11-10T17:35:18</PublishDateTimeInUTC>
<LastEventDateTimeInUTC>2012-11-11T13:58:52.055</LastEventDateTimeInUTC>
<Events>
<CloudLibraryEvent>
<EventId>4302fcca-ef99-49bf-bd29-d673e990f4a7</EventId>
<EventType>CHECKIN</EventType>
<EventStartDateTimeInUTC>2024-11-10T05:07:56</EventStartDateTimeInUTC>
<EventEndDateTimeInUTC>2024-11-10T07:50:59</EventEndDateTimeInUTC>
<ItemId>edbz9</ItemId>
<ItemLibraryId>1234</ItemLibraryId>
<ISBN>9780307238405</ISBN>
<PatronId>TestUser1</PatronId>
<PatronLibraryId>1234</PatronLibraryId>
<EventPublishDateTimeInUTC>2024-11-10T17:35:18</EventPublishDateTimeInUTC>
</CloudLibraryEvent>
</Events>
</LibraryEventBatch>
"""


@freeze_time("2024-11-11 10:00:00")
class TestCloudLibraryClient:
    @pytest.fixture
    def test_instance(self):
        return CloudLibraryClient(
            "library_id", "account_id", "account_key")

    def test_get_library_events_success_no_args(
            self, test_instance, mocker, caplog):
        start = "2024-11-10T10:00:00"
        end = "2024-11-11T10:00:00"
        mock_request = mocker.patch(
            "nypl_py_utils.classes.cloudlibrary_client.CloudLibraryClient.request", # noqa
            return_value=_TEST_LIBRARY_EVENTS_RESPONSE)
        response = test_instance.get_library_events()

        mock_request.assert_called_once_with(
            path=f"data/cloudevents?startdate={start}&enddate={end}",
            method_type="GET")
        assert response == _TEST_LIBRARY_EVENTS_RESPONSE
        assert (f"Fetching all library events in time frame "
                f"{start} to {end}...") in caplog.text

    def test_get_library_events_success_with_start_and_end_date(
            self, test_instance, mocker, caplog):
        start = "2024-11-01T10:00:00"
        end = "2024-11-05T10:00:00"
        mock_request = mocker.patch(
            "nypl_py_utils.classes.cloudlibrary_client.CloudLibraryClient.request", # noqa
            return_value=_TEST_LIBRARY_EVENTS_RESPONSE)
        response = test_instance.get_library_events(start, end)

        mock_request.assert_called_once_with(
            path=f"data/cloudevents?startdate={start}&enddate={end}",
            method_type="GET")
        assert response == _TEST_LIBRARY_EVENTS_RESPONSE
        assert (f"Fetching all library events in time frame "
                f"{start} to {end}...") in caplog.text

    def test_get_library_events_success_with_no_end_date(
            self, test_instance, mocker, caplog):
        start = "2024-11-01T09:00:00"
        end = "2024-11-11T10:00:00"
        mock_request = mocker.patch(
            "nypl_py_utils.classes.cloudlibrary_client.CloudLibraryClient.request", # noqa
            return_value=_TEST_LIBRARY_EVENTS_RESPONSE)
        response = test_instance.get_library_events(start)

        mock_request.assert_called_once_with(
            path=f"data/cloudevents?startdate={start}&enddate={end}",
            method_type="GET")
        assert response == _TEST_LIBRARY_EVENTS_RESPONSE
        assert (f"Fetching all library events in time frame "
                f"{start} to {end}...") in caplog.text

    def test_get_library_events_exception_when_start_date_greater_than_end(
            self, test_instance, caplog):
        start = "2024-11-11T09:00:00"
        end = "2024-11-01T10:00:00"

        with pytest.raises(CloudLibraryClientError):
            test_instance.get_library_events(start, end)
        assert (f"Start date {start} greater than end date "
                f"{end}, cannot retrieve library events") in caplog.text

    def test_get_library_events_exception_when_connection_timeout(
            self, test_instance, requests_mock):
        start = "2024-11-10T10:00:00"
        end = "2024-11-11T10:00:00"

        # We're making sure that a separate error during a sub-method will
        # still result in CloudLibraryClientError
        requests_mock.get(
            f"{_API_URL}{test_instance.library_id}/data/cloudevents?startdate={start}&enddate={end}",  # noqa
            exc=ConnectTimeout)

        with pytest.raises(CloudLibraryClientError):
            test_instance.get_library_events()

    def test_request_success(self, test_instance, mocker):
        start = "2024-11-10T10:00:00"
        end = "2024-11-11T10:00:00"
        expected_headers = {'3mcl-Datetime': 'Mon, 11 Nov 2024 10:00:00 GMT',
                            '3mcl-Authorization': '3MCLAUTH account_id:KipNmbVsmsT2xPjP4oHAaR3n00JgcszfF6mQRffBoRk=', # noqa
                            '3mcl-APIVersion': '3.0.2',
                            'Accept': 'application/xml'}
        mock_get = mocker.patch("requests.sessions.Session.get")
        test_instance.request(
            path=f"data/cloudevents?startdate={start}&enddate={end}",
            method_type="GET")

        mock_get.assert_called_once_with(
            url=f"{_API_URL}library_id/data/cloudevents?startdate={start}&enddate={end}", # noqa
            data=None,
            headers=expected_headers,
            timeout=60)

    def test_request_failure(self, test_instance, requests_mock, caplog):
        start = "2024-11-10T10:00:00"
        end = "2024-11-11T10:00:00"
        requests_mock.get(
            f"{_API_URL}{test_instance.library_id}/data/cloudevents?startdate={start}&enddate={end}",  # noqa
            exc=ConnectTimeout)

        with pytest.raises(CloudLibraryClientError):
            test_instance.request(
                path=f"data/cloudevents?startdate={start}&enddate={end}",
                method_type="GET")

    def test_create_request_body_success(self, test_instance):
        request_type = "CheckoutRequest"
        item_id = "df45qw"
        patron_id = "215555602845"
        EXPECTED_REQUEST_BODY = (f"<{request_type}><ItemId>{item_id}</ItemId>"
                                 f"<PatronId>{patron_id}</PatronId>"
                                 f"</{request_type}>")
        request_body = test_instance.create_request_body(
            request_type, item_id, patron_id)

        assert request_body == EXPECTED_REQUEST_BODY
