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
            self, test_instance, mocker):
        mock_request = mocker.patch(
            "nypl_py_utils.classes.cloudlibrary_client.CloudLibraryClient.request") # noqa
        test_instance.get_library_events()

        mock_request.assert_called_once_with(
            path="data/cloudevents",
            method_type="GET")

    def test_get_library_events_success_with_start_and_end_date(
            self, test_instance, mocker):
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

    def test_get_library_events_exception_when_start_date_greater_than_end(
            self, test_instance, caplog):
        start = "2024-11-11T09:00:00"
        end = "2024-11-01T10:00:00"

        with pytest.raises(CloudLibraryClientError):
            test_instance.get_library_events(start, end)
        assert (f"Start date {start} greater than end date {end}, "
                f"cannot retrieve library events") in caplog.text

    def test_get_library_events_exception_when_connection_timeout(
            self, test_instance, requests_mock, caplog):
        start = "2024-11-10T10:00:00"
        end = "2024-11-11T10:00:00"
        url = f"{_API_URL}{test_instance.library_id}/data/cloudevents?startdate={start}&enddate={end}"  # noqa

        # We're making sure that a separate error during a sub-method will
        # still result in CloudLibraryClientError
        requests_mock.get(
            url, exc=ConnectTimeout)

        with pytest.raises(CloudLibraryClientError):
            test_instance.get_library_events(start, end)
        assert (f"Failed to retrieve response from {url}") in caplog.text

    def test_get_request_success(self, test_instance, requests_mock):
        start = "2024-11-10T10:00:00"
        end = "2024-11-11T10:00:00"
        url = f"{_API_URL}{test_instance.library_id}/data/cloudevents?startdate={start}&enddate={end}" # noqa
        expected_headers = {"3mcl-Datetime": "Mon, 11 Nov 2024 10:00:00 GMT",
                            "3mcl-Authorization": "3MCLAUTH account_id:KipNmbVsmsT2xPjP4oHAaR3n00JgcszfF6mQRffBoRk=", # noqa
                            "3mcl-APIVersion": "3.0.2",
                            "Accept": "application/xml"}
        requests_mock.get(
            url=url, text=_TEST_LIBRARY_EVENTS_RESPONSE)

        response = test_instance.request(
            path=f"data/cloudevents?startdate={start}&enddate={end}",
            method_type="GET")

        assert response.text == _TEST_LIBRARY_EVENTS_RESPONSE
        assert requests_mock.request_history[0].method == "GET"
        assert requests_mock.request_history[0].url == url
        assert requests_mock.request_history[0].body is None
        assert expected_headers.items() <= dict(
            requests_mock.request_history[0].headers).items()

    def test_put_request_success(self, test_instance, requests_mock):
        start = "2024-11-10T10:00:00"
        end = "2024-11-11T10:00:00"
        url = f"{_API_URL}{test_instance.library_id}/data/cloudevents?startdate={start}&enddate={end}" # noqa
        expected_headers = {"3mcl-Datetime": "Mon, 11 Nov 2024 10:00:00 GMT",
                            "3mcl-Authorization": "3MCLAUTH account_id:3M773C6ZVWmB/ISoSjQy9iBp48T4tUWhoNOwXaseMtE=", # noqa
                            "3mcl-APIVersion": "3.0.2",
                            "Content-Type": "application/xml"}
        requests_mock.put(
            url=url, text=_TEST_LIBRARY_EVENTS_RESPONSE)

        response = test_instance.request(
            path=f"data/cloudevents?startdate={start}&enddate={end}",
            method_type="PUT",
            body={"test": "test"})

        assert response.text == _TEST_LIBRARY_EVENTS_RESPONSE
        assert requests_mock.request_history[0].method == "PUT"
        assert requests_mock.request_history[0].url == url
        assert requests_mock.request_history[0].body == "test=test"
        assert expected_headers.items() <= dict(
            requests_mock.request_history[0].headers).items()

    def test_post_request_success(self, test_instance, requests_mock):
        start = "2024-11-10T10:00:00"
        end = "2024-11-11T10:00:00"
        url = f"{_API_URL}{test_instance.library_id}/data/cloudevents?startdate={start}&enddate={end}" # noqa
        expected_headers = {"3mcl-Datetime": "Mon, 11 Nov 2024 10:00:00 GMT",
                            "3mcl-Authorization": "3MCLAUTH account_id:vF0zI6ee1w1PbTLQ9EVvtxRly2vpCRxdBdAHb8DZQ4E=", # noqa
                            "3mcl-APIVersion": "3.0.2",
                            "Content-Type": "application/xml"}
        requests_mock.post(
            url=url, text=_TEST_LIBRARY_EVENTS_RESPONSE)

        response = test_instance.request(
            path=f"data/cloudevents?startdate={start}&enddate={end}",
            method_type="POST",
            body={"test": "test"})

        assert response.text == _TEST_LIBRARY_EVENTS_RESPONSE
        assert requests_mock.request_history[0].method == "POST"
        assert requests_mock.request_history[0].url == url
        assert requests_mock.request_history[0].body == "test=test"
        assert expected_headers.items() <= dict(
            requests_mock.request_history[0].headers).items()

    def test_request_failure(self, test_instance,
                             requests_mock, caplog):
        start = "2024-11-10T10:00:00"
        end = "2024-11-11T10:00:00"
        url = f"{_API_URL}{test_instance.library_id}/data/cloudevents?startdate={start}&enddate={end}" # noqa
        requests_mock.get(
            url, exc=ConnectTimeout)

        with pytest.raises(CloudLibraryClientError):
            test_instance.request(
                path=f"data/cloudevents?startdate={start}&enddate={end}",
                method_type="GET")
        assert (f"Failed to retrieve response from "
                f"{url}: ConnectTimeout()") in caplog.text

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
