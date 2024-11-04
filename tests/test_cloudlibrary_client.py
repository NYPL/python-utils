from unittest import mock
import pytest

from nypl_py_utils.classes.cloudlibrary_client import CloudLibraryClient

_TEST_LIBRARY_EVENTS_RESPONSE = """<LibraryEventBatch xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/20
01/XMLSchema-instance">
<PublishId>4302fcca-ef99-49bf-bd29-d673e990f765</PublishId>
<PublishDateTimeInUTC>2012-06-29T17:35:18</PublishDateTimeInUTC>
<LastEventDateTimeInUTC>2012-06-26T13:58:52.055</LastEventDateTimeInUTC>
<Events>
<CloudLibraryEvent>
<EventId>4302fcca-ef99-49bf-bd29-d673e990f4a7</EventId>
<EventType>CHECKIN</EventType>
<EventStartDateTimeInUTC>2012-06-26T05:07:56</EventStartDateTimeInUTC>
<EventEndDateTimeInUTC>2012-06-26T07:50:59</EventEndDateTimeInUTC>
<ItemId>edbz9</ItemId>
<ItemLibraryId>1234</ItemLibraryId>
<ISBN>9780307238405</ISBN>
<PatronId>TestUser1</PatronId>
<PatronLibraryId>1234</PatronLibraryId>
<EventPublishDateTimeInUTC>2012-06-29T17:35:18</EventPublishDateTimeInUTC>
</CloudLibraryEvent>
</Events>
</LibraryEventBatch>
"""


class TestCloudLibraryClient:
    @pytest.fixture
    def test_instance(self):
        client = CloudLibraryClient("library_id", "account_id", "account_key")
        client.request = mock.MagicMock()
        return client

    def test_get_library_events_success(self, test_instance):
        return
