import pandas as pd

from nypl_py_utils.functions.log_helper import create_log

logger = create_log("patron_data_helpers")

_REDSHIFT_QUERY = """
    SELECT patron_id, postal_code, geoid
    FROM {table}
    WHERE patron_id IN ({ids});"""

_SIERRA_BARCODES_TO_IDS_QUERY = """
    SELECT index_tag || index_entry, record_id
    FROM sierra_view.phrase_entry
    WHERE index_tag || index_entry IN ({});"""

_SIERRA_PATRON_DATA_QUERY = """
    SELECT id, record_num, barcode, ptype_code, pcode3,
    CASE WHEN LENGTH(TRIM(home_library_code)) = 0
        OR TRIM(home_library_code) = 'none' THEN NULL
        ELSE TRIM(home_library_code) END
    FROM sierra_view.patron_view
    WHERE {id_field} IN ({ids});"""


def barcodes_to_patron_ids(sierra_client, barcodes, isolate_connection=True,
                           remove_duplicates=True):
    """
    Converts barcodes into Sierra patron ids

    Parameters
    ----------
    sierra_client: PostgreSQLClient
        The client with which to query Sierra
    barcodes: sequence of strings
        The sequence of barcodes to be mapped. Must be iterable and without
        'None' entries. Each barcode is expected to be a string without a
        prepending 'b' character.
    isolate_connection: bool, optional
        Whether the database connection should be opened and closed within this
        method or whether it will be handled by the user
    remove_duplicates: bool, optional
        Whether barcodes that map to multiple patron ids should be removed

    Returns
    -------
    DataFrame
        A pandas DataFrame with 'barcode' and 'patron_id' columns. The
        'patron_id' column is set to be a string.
    """
    unique_barcodes = set(barcodes)
    if unique_barcodes:
        logger.info(f"Mapping ({len(unique_barcodes)}) barcodes to patron ids")
        barcodes_str = "'b" + "','b".join(unique_barcodes) + "'"
        if isolate_connection:
            sierra_client.connect()
        raw_data = sierra_client.execute_query(
            _SIERRA_BARCODES_TO_IDS_QUERY.format(barcodes_str))
        if isolate_connection:
            sierra_client.close_connection()
    else:
        logger.info("No barcodes given with which to query Sierra")
        raw_data = []

    df = pd.DataFrame(raw_data, columns=["barcode", "patron_id"])
    df = df[pd.notnull(df[["barcode", "patron_id"]]).all(axis=1)]
    df["barcode"] = df["barcode"].str.lstrip("b")
    df["patron_id"] = df["patron_id"].astype("Int64").astype("string")
    df = df.drop_duplicates()
    if remove_duplicates:
        return df.drop_duplicates("barcode", keep=False)
    else:
        return df


def get_sierra_patron_data_from_ids(sierra_client, ids,
                                    isolate_connection=True,
                                    remove_duplicates=False,
                                    use_record_num=False):
    """
    Given Sierra patron ids, returns standard patron fields from Sierra

    Parameters
    ----------
    sierra_client: PostgreSQLClient
        The client with which to query Sierra
    ids: sequence of strings
        The sequence of patron ids or record_nums to be fetched. Must be
        iterable and without any 'None' entries. Each id is expected to be a
        string.
    isolate_connection: bool, optional
        Whether the database connection should be opened and closed within this
        method or whether it will be handled by the user
    remove_duplicates: bool, optional
        Whether patron ids that map to multiple rows with different values
        should be removed
    use_record_num: bool, optional
        Whether the `ids` given are record_nums rather than patron ids

    Returns
    -------
    DataFrame
        A pandas DataFrame with standard patron columns. The 'patron_id' column
        is set to be a string.
    """
    unique_ids = set(ids)
    if unique_ids:
        logger.info(
            f"Fetching Sierra patron data for ({len(unique_ids)}) patrons")
        id_field = "record_num" if use_record_num else "id"
        ids_str = ",".join(unique_ids)
        if isolate_connection:
            sierra_client.connect()
        raw_data = sierra_client.execute_query(
            _SIERRA_PATRON_DATA_QUERY.format(id_field=id_field, ids=ids_str))
        if isolate_connection:
            sierra_client.close_connection()
    else:
        logger.info("No patron ids given with which to query Sierra")
        raw_data = []

    df = pd.DataFrame(raw_data, columns=[
        "patron_id", "record_num", "barcode", "ptype_code", "pcode3",
        "patron_home_library_code"])
    df = df[pd.notnull(df["patron_id"])]
    df["patron_id"] = df["patron_id"].astype("Int64").astype("string")
    if use_record_num:
        df = df[pd.notnull(df["record_num"])]
        df["record_num"] = df["record_num"].astype("Int32").astype("string")

    if not remove_duplicates:
        return df.drop_duplicates()
    elif use_record_num:
        # If one patron id maps to two rows that are identical except for the
        # barcode, arbitrarily delete one of the rows
        df = df.drop_duplicates(
            ["patron_id", "record_num", "ptype_code", "pcode3",
             "patron_home_library_code"])
        return df.drop_duplicates("record_num", keep=False)
    else:
        # If one patron id maps to two rows that are identical except for the
        # barcode or record_num, arbitrarily delete one of the rows
        df = df.drop_duplicates(
            ["patron_id", "ptype_code", "pcode3", "patron_home_library_code"])
        return df.drop_duplicates("patron_id", keep=False)


def get_sierra_patron_data_from_barcodes(sierra_client, barcodes,
                                         isolate_connection=True):
    """
    Given barcodes, returns standard patron fields from Sierra. One row per
    barcode is returned for all barcodes found in Sierra.

    Parameters
    ----------
    sierra_client: PostgreSQLClient
        The client with which to query Sierra
    barcodes: sequence of strings
        The sequence of barcodes to be mapped. Must be iterable and without
        'None' entries. Each barcode is expected to be a string without a
        prepending 'b' character.
    isolate_connection: bool, optional
        Whether the database connection should be opened and closed within this
        method or whether it will be handled by the user

    Returns
    -------
    DataFrame
        A pandas DataFrame with barcodes plus the standard patron columns. The
        'patron_id' column is set to be a string.
    """
    if isolate_connection:
        sierra_client.connect()
    barcode_patron_id_df = barcodes_to_patron_ids(
        sierra_client, barcodes, False, True)
    patron_data_df = get_sierra_patron_data_from_ids(
        sierra_client, barcode_patron_id_df["patron_id"], False, False, False)
    if isolate_connection:
        sierra_client.close_connection()

    # If one patron id maps to two rows that are identical except for the
    # barcode or record_num, arbitrarily delete one of the rows
    patron_data_df = patron_data_df.drop_duplicates(
        ["patron_id", "ptype_code", "pcode3", "patron_home_library_code"])

    # Prefer matches where both the barcode and the patron id match. Otherwise,
    # accept matches where only the patron id matches. If more than one match
    # is found, use none of them and NULL out the patron fields.
    df = barcode_patron_id_df.merge(
        patron_data_df, how="left", on=["patron_id", "barcode"],
        indicator=True
    )
    perfect_match_df = df[df["_merge"] == "both"].drop(columns=["_merge"])
    imperfect_match_df = df[["barcode", "patron_id"]].drop(
        perfect_match_df.index).merge(patron_data_df.drop(columns=["barcode"]),
                                      how="left", on="patron_id")
    df = pd.concat([perfect_match_df, imperfect_match_df], ignore_index=True)
    df.loc[df.duplicated("barcode", keep=False), [
        "record_num", "ptype_code", "pcode3",
        "patron_home_library_code"]] = None
    return df.drop_duplicates("barcode")


def get_redshift_patron_data(redshift_client, obfuscated_patron_ids,
                             isolate_connection=True):
    """
    Given obfuscated patron ids, returns postal code and geoid from Redshift.
    One row per patron id is returned for all patron ids found in Redshift.

    Parameters
    ----------
    redshift_client: RedshiftClient
        The client with which to query Redshift
    obfuscated_patron_ids: sequence of strings
        The sequence of patron ids to be mapped. Must be iterable and without
        'None' entries. Each patron id is expected to have been obfuscated.
    isolate_connection: bool, optional
        Whether the database connection should be opened and closed within this
        method or whether it will be handled by the user

    Returns
    -------
    DataFrame
        A pandas DataFrame with 'patron_id', 'postal_code', and 'geoid' columns
    """
    unique_patron_ids = set(obfuscated_patron_ids)
    if unique_patron_ids:
        logger.info(f"Querying Redshift for ({len(unique_patron_ids)}) "
                    "patrons")
        redshift_table = "patron_info"
        if redshift_client.database != "production":
            redshift_table += "_" + redshift_client.database
        patron_ids_str = "'" + "','".join(unique_patron_ids) + "'"

        if isolate_connection:
            redshift_client.connect()
        raw_data = redshift_client.execute_query(
            _REDSHIFT_QUERY.format(table=redshift_table, ids=patron_ids_str))
        if isolate_connection:
            redshift_client.close_connection()
    else:
        logger.info("No patron ids given with which to query Redshift")
        raw_data = []

    df = pd.DataFrame(raw_data, columns=["patron_id", "postal_code", "geoid"])
    df = df[pd.notnull(df["patron_id"])]
    if not df["patron_id"].is_unique:
        duplicates = df.loc[df.duplicated("patron_id"), "patron_id"]
        logger.warning(
            "More than one Redshift row found for the following patron ids: "
            f"{', '.join(duplicates)}")
        return df.drop_duplicates("patron_id", keep=False)
    else:
        return df
