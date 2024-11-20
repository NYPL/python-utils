import logging
import pandas as pd

from nypl_py_utils.functions.patron_data_helper import (
    barcodes_to_patron_ids,
    get_redshift_patron_data,
    get_sierra_patron_data_from_barcodes,
    get_sierra_patron_data_from_ids)
from pandas.testing import assert_frame_equal, assert_series_equal

_TEST_REDSHIFT_RESPONSE = [
    ["obf1", "1"*5, "1"*11], ["obf2", None, "2"*11], ["obf3", "3"*5, None],
    [None, "4"*5, "4"*11],
]

_TEST_SIERRA_BARCODE_RESPONSE = [
    ("b1", 1), ("b2", 2), ("b3", 3), ("b33", 3), ("b4", 4), ("b4", 44),
    ("b5", None), (None, 5),
]

_TEST_SIERRA_IDS_RESPONSE = [
    (1, "b1", 11, 12, "aa"), (2, "b2", 21, 22, "bb"),
    (3, "b3", 31, 32, "cc"), (33, "b3", 331, 332, "ccc"),
    (4, None, None, None, None), (5, "b5", 51, 52, "dd"),
    (6, "b6", 61, 62, "ee"), (6, "b66", 61, 62, "ee"),
    (7, "b7", 71, 72, "ff"), (7, "b77", 771, 772, "ffff"),
    (None, "b4", None, None, None), (5, "b5", 51, 52, "dd"),
]

_TEST_BARCODE_DF = pd.DataFrame(
    [[f"b{i}", str(i)] for i in range(1, 10)],
    columns=["barcode", "patron_id"])
_TEST_BARCODE_DF["patron_id"] = _TEST_BARCODE_DF["patron_id"].astype("string")

_TEST_ID_DF = pd.DataFrame(
    [["1", "b1", 11, 12, "aa"],  # one perfect match
     ["2", "b5", 21, 22, "bb"],  # different id and barcode matches
     # no match for patron id 3
     ["4", "b4", 41, 42, "dd"],  # two matches -- one perfect, one imperfect
     ["4", "b444", 43, 44, "dddd"],
     ["5", "b555", 51, 52, "eeee"],  # two matches -- both imperfect
     ["5", "b556", 53, 54, "eeef"],
     ["6", "b6", 61, 62, "ffff"],  # two matches -- both perfect
     ["6", "b6", 63, 64, "fffg"],
     ["7", "b777", 71, 72, "gg"],  # two matches -- same except barcode
     ["7", "b778", 71, 72, "gg"],
     ["8", None, 81, 82, "hh"],  # one imperfect match/no barcode
     ["9", "b9", None, None, None]],  # one perfect match/all null fields
    columns=["patron_id", "barcode", "ptype_code", "pcode3",
             "patron_home_library_code"])
_TEST_ID_DF["patron_id"] = _TEST_ID_DF["patron_id"].astype("string")


class TestPatronDataHelper:

    def test_barcodes_to_patron_ids(self, mocker):
        RESULT = pd.DataFrame(
            [["1", "1"], ["2", "2"], ["3", "3"], ["33", "3"]],
            columns=["barcode", "patron_id"])
        RESULT["patron_id"] = RESULT["patron_id"].astype("string")

        mock_sierra_client = mocker.MagicMock()
        mock_sierra_client.execute_query.return_value = \
            _TEST_SIERRA_BARCODE_RESPONSE

        assert_frame_equal(
            RESULT, barcodes_to_patron_ids(
                mock_sierra_client, [str(el) for el in range(1, 8)] + ["1",]
            ))

        mock_sierra_client.connect.assert_called_once()
        mock_sierra_client.execute_query.assert_called_once()
        mock_sierra_client.close_connection.assert_called_once()

        # Because the set of barcodes is unordered, it can't be tested
        # directly. The workaround is to test the total length of the query
        # plus that each barcode appears in it.
        query = mock_sierra_client.execute_query.call_args[0][0]
        assert len(query) == 157
        for el in range(1, 8):
            assert f"'b{el}'" in query

    def test_barcodes_to_patron_ids_unisolated(self, mocker):
        mock_sierra_client = mocker.MagicMock()
        mock_sierra_client.execute_query.return_value = []

        barcodes_to_patron_ids(mock_sierra_client, ["1",],
                               isolate_connection=False)

        mock_sierra_client.connect.assert_not_called()
        mock_sierra_client.execute_query.assert_called_once()
        mock_sierra_client.close_connection.assert_not_called()

    def test_barcodes_to_patron_ids_with_duplicates(self, mocker):
        RESULT = pd.DataFrame(
            [["1", "1"], ["2", "2"], ["3", "3"],
             ["33", "3"], ["4", "4"], ["4", "44"]],
            columns=["barcode", "patron_id"])
        RESULT["patron_id"] = RESULT["patron_id"].astype("string")

        mock_sierra_client = mocker.MagicMock()
        mock_sierra_client.execute_query.return_value = \
            _TEST_SIERRA_BARCODE_RESPONSE

        assert_frame_equal(
            RESULT, barcodes_to_patron_ids(
                mock_sierra_client, [str(el) for el in range(1, 7)],
                remove_duplicates=False
            ))

    def test_get_sierra_patron_data_from_ids(self, mocker):
        RESULT = pd.DataFrame(
            [["1", "b1", 11, 12, "aa"], ["2", "b2", 21, 22, "bb"],
             ["3", "b3", 31, 32, "cc"], ["33", "b3", 331, 332, "ccc"],
             ["4", None, None, None, None],
             ["5", "b5", 51, 52, "dd"], ["6", "b6", 61, 62, "ee"],
             ["6", "b66", 61, 62, "ee"], ["7", "b7", 71, 72, "ff"],
             ["7", "b77", 771, 772, "ffff"]],
            columns=["patron_id", "barcode", "ptype_code", "pcode3",
                     "patron_home_library_code"])
        RESULT["patron_id"] = RESULT["patron_id"].astype("string")

        mock_sierra_client = mocker.MagicMock()
        mock_sierra_client.execute_query.return_value = \
            _TEST_SIERRA_IDS_RESPONSE

        assert_frame_equal(
            RESULT, get_sierra_patron_data_from_ids(
                mock_sierra_client, [str(el) for el in range(1, 9)] + ["1",]
            ))

        mock_sierra_client.connect.assert_called_once()
        mock_sierra_client.execute_query.assert_called_once()
        mock_sierra_client.close_connection.assert_called_once()

        # Because the set of patron ids is unordered, it can't be tested
        # directly. The workaround is to test the total length of the query
        # plus that each id appears in it.
        query = mock_sierra_client.execute_query.call_args[0][0]
        assert len(query) == 257
        for el in range(1, 9):
            assert str(el) in query

    def test_get_sierra_patron_data_from_ids_unisolated(self, mocker):
        mock_sierra_client = mocker.MagicMock()
        mock_sierra_client.execute_query.return_value = []

        get_sierra_patron_data_from_ids(mock_sierra_client, ["1",],
                                        isolate_connection=False)

        mock_sierra_client.connect.assert_not_called()
        mock_sierra_client.execute_query.assert_called_once()
        mock_sierra_client.close_connection.assert_not_called()

    def test_get_sierra_patron_data_from_ids_without_duplicates(self, mocker):
        RESULT = pd.DataFrame(
            [["1", "b1", 11, 12, "aa"], ["2", "b2", 21, 22, "bb"],
             ["3", "b3", 31, 32, "cc"], ["33", "b3", 331, 332, "ccc"],
             ["4", None, None, None, None], ["5", "b5", 51, 52, "dd"],
             ["6", "b6", 61, 62, "ee"]],
            columns=["patron_id", "barcode", "ptype_code", "pcode3",
                     "patron_home_library_code"])
        RESULT["patron_id"] = RESULT["patron_id"].astype("string")

        mock_sierra_client = mocker.MagicMock()
        mock_sierra_client.execute_query.return_value = \
            _TEST_SIERRA_IDS_RESPONSE

        assert_frame_equal(
            RESULT, get_sierra_patron_data_from_ids(
                mock_sierra_client, [str(el) for el in range(1, 9)],
                remove_duplicates=True
            ))

    def test_get_sierra_patron_data_from_barcodes(self, mocker):
        RESULT = pd.DataFrame(
            [["b1", "1", 11, 12, "aa"],
             ["b4", "4", 41, 42, "dd"],
             ["b6", "6", None, None, None],
             ["b9", "9", None, None, None],
             ["b2", "2", 21, 22, "bb"],
             ["b3", "3", None, None, None],
             ["b5", "5", None, None, None],
             ["b7", "7", 71, 72, "gg"],
             ["b8", "8", 81, 82, "hh"]],
            columns=["barcode", "patron_id", "ptype_code", "pcode3",
                     "patron_home_library_code"])
        RESULT["patron_id"] = RESULT["patron_id"].astype("string")
        TEST_BARCODES = [f"b{i}" for i in range(1, 11)] + ["b1",]
        TEST_IDS = pd.Series([str(i) for i in range(1, 10)],
                             dtype="string", name="patron_id")
        mocked_barcodes_method = mocker.patch(
            "nypl_py_utils.functions.patron_data_helper.barcodes_to_patron_ids",  # noqa: E501
            return_value=_TEST_BARCODE_DF)
        mocked_ids_method = mocker.patch(
            "nypl_py_utils.functions.patron_data_helper.get_sierra_patron_data_from_ids",  # noqa: E501
            return_value=_TEST_ID_DF)
        mock_sierra_client = mocker.MagicMock()

        assert_frame_equal(
            RESULT,
            get_sierra_patron_data_from_barcodes(
                mock_sierra_client, TEST_BARCODES).reset_index(drop=True),
            check_like=True)

        mock_sierra_client.connect.assert_called_once()
        mock_sierra_client.close_connection.assert_called_once()

        mocked_barcodes_method.assert_called_once_with(
            mock_sierra_client, TEST_BARCODES, False, True)
        assert mocked_ids_method.call_args[0][0] == mock_sierra_client
        assert_series_equal(mocked_ids_method.call_args[0][1], TEST_IDS)
        assert mocked_ids_method.call_args[0][2] is False
        assert mocked_ids_method.call_args[0][3] is False

    def test_get_sierra_patron_data_from_barcodes_unisolated(self, mocker):
        mocker.patch(
            "nypl_py_utils.functions.patron_data_helper.barcodes_to_patron_ids",  # noqa: E501
            return_value=pd.DataFrame([], columns=["barcode", "patron_id"]))
        mocker.patch(
            "nypl_py_utils.functions.patron_data_helper.get_sierra_patron_data_from_ids",  # noqa: E501
            return_value=pd.DataFrame(
                [], columns=["patron_id", "barcode", "ptype_code", "pcode3",
                             "patron_home_library_code"]))
        mock_sierra_client = mocker.MagicMock()

        get_sierra_patron_data_from_barcodes(
            mock_sierra_client, ["1",], isolate_connection=False)

        mock_sierra_client.connect.assert_not_called()
        mock_sierra_client.close_connection.assert_not_called()

    def test_get_redshift_patron_data(self, mocker, caplog):
        RESULT = pd.DataFrame(
            [["obf1", "1"*5, "1"*11], ["obf2", None, "2"*11],
             ["obf3", "3"*5, None]],
            columns=["patron_id", "postal_code", "geoid"])

        mock_redshift_client = mocker.MagicMock()
        mock_redshift_client.database = "test_db"
        mock_redshift_client.execute_query.return_value = \
            _TEST_REDSHIFT_RESPONSE

        with caplog.at_level(logging.WARNING):
            assert_frame_equal(
                RESULT, get_redshift_patron_data(
                    mock_redshift_client,
                    ["obf1", "obf2", "obf3", "obf4", "obf1"]
                ))

        assert caplog.text == ""
        mock_redshift_client.connect.assert_called_once()
        mock_redshift_client.execute_query.assert_called_once()
        mock_redshift_client.close_connection.assert_called_once()

        # Because the set of patron ids is unordered, it can't be tested
        # directly. The workaround is to test the total length of the query
        # plus that each id appears in it.
        query = mock_redshift_client.execute_query.call_args[0][0]
        assert len(query) == 124
        assert "patron_info_test_db" in query
        for el in ["'obf1'", "'obf2'", "'obf3'", "'obf4'"]:
            assert el in query

    def test_get_redshift_patron_data_unisolated(self, mocker):
        mock_redshift_client = mocker.MagicMock()
        mock_redshift_client.execute_query.return_value = []

        get_redshift_patron_data(mock_redshift_client, ["1",],
                                 isolate_connection=False)

        mock_redshift_client.connect.assert_not_called()
        mock_redshift_client.execute_query.assert_called_once()
        mock_redshift_client.close_connection.assert_not_called()

    def test_get_redshift_patron_data_with_duplicates(self, mocker, caplog):
        RESULT = pd.DataFrame(
            [["obf1", "1"*5, "1"*11], ["obf2", None, "2"*11],
             ["obf3", "3"*5, None]],
            columns=["patron_id", "postal_code", "geoid"])

        mock_redshift_client = mocker.MagicMock()
        mock_redshift_client.execute_query.return_value = \
            _TEST_REDSHIFT_RESPONSE + [["obf4", "bad_zip", "bad_geoid"],
                                       ["obf4", "bad_zip2", "bad_geoid2"]]

        with caplog.at_level(logging.WARNING):
            assert_frame_equal(
                RESULT, get_redshift_patron_data(
                    mock_redshift_client,
                    ["obf1", "obf2", "obf3", "obf4"]
                ))

        assert ("More than one Redshift row found for the following patron "
                "ids: obf4") in caplog.text
