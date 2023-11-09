import os
import re
import requests
from requests.exceptions import JSONDecodeError, RequestException

CACHE = {}


def parse_research_catalog_identifier(identifier: str):
    """
    Given a RC identifier (e.g. "b1234", "pb9876", "pi4567"), returns a dict
    defining:
     - nyplSource: One of sierra-nypl, recap-pul, recap-cul, or recap-hl (at
       writing)
     - nyplType: One of bib, holding, or item
     - id: The numeric string id
    """
    if not isinstance(identifier, str):
        raise ResearchCatalogIdentifierError(
            f'Invalid RC identifier: {identifier}')

    # Extract prefix from the identifier:
    match = re.match(r'^([a-z]+)', identifier)
    if match is None:
        raise ResearchCatalogIdentifierError(
                f'Invalid RC identifier: {identifier}')
    prefix = match[0]

    # The id is the identifier without the prefix:
    id = identifier.replace(prefix, '')
    nyplType = None
    nyplSource = None

    # Look up nyplType and nyplSource in nypl-core based on the prefix:
    for _nyplSource, mapping in nypl_core_source_mapping().items():
        if mapping.get('bibPrefix') == prefix:
            nyplType = 'bib'
        elif mapping.get('itemPrefix') == prefix:
            nyplType = 'item'
        elif mapping.get('holdingPrefix') == prefix:
            nyplType = 'holding'
        if nyplType is not None:
            nyplSource = _nyplSource
            break

    if nyplSource is None:
        raise ResearchCatalogIdentifierError(
                f'Invalid RC identifier: {identifier}')

    return {
        'nyplSource': nyplSource,
        'nyplType': nyplType,
        'id': id
    }


def research_catalog_id_prefix(nyplSource: str, nyplType='bib'):
    """
    Given a nyplSource (e.g. 'sierra-nypl') and nyplType (e.g. 'item'), returns
    the relevant prefix used in the RC identifier (e.g. 'i')
    """
    if nypl_core_source_mapping().get(nyplSource) is None:
        raise ResearchCatalogIdentifierError(
                f'Invalid nyplSource: {nyplSource}')

    if not isinstance(nyplType, str):
        raise ResearchCatalogIdentifierError(
            f'Invalid nyplType: {nyplType}')

    prefixKey = f'{nyplType}Prefix'
    if nypl_core_source_mapping()[nyplSource].get(prefixKey) is None:
        raise ResearchCatalogIdentifierError(f'Invalid nyplType: {nyplType}')

    return nypl_core_source_mapping()[nyplSource][prefixKey]


def nypl_core_source_mapping():
    """
    Builds a nypl-source-mapping by retrieving the mapping from NYPL-Core
    """
    name = 'nypl-core-source-mapping'
    if not CACHE.get(name) is None:
        return CACHE[name]

    url = os.environ.get('NYPL_CORE_SOURCE_MAPPING_URL',
            'https://raw.githubusercontent.com/NYPL/nypl-core/master/mappings/recap-discovery/nypl-source-mapping.json') # noqa
    try:
        response = requests.get(url)
        response.raise_for_status()
    except RequestException as e:
        raise ResearchCatalogIdentifierError(
            'Failed to retrieve nypl-core source-mapping file from {url}:'
            ' {errorType} {errorMessage}'
            .format(url=url, errorType=type(e), errorMessage=e)) from None

    try:
        CACHE[name] = response.json()
        return CACHE[name]
    except (JSONDecodeError, KeyError) as e:
        raise ResearchCatalogIdentifierError(
            'Failed to parse nypl-core source-mapping file: {errorType}'
            ' {errorMessage}'
            .format(errorType=type(e), errorMessage=e)) from None


class ResearchCatalogIdentifierError(Exception):
    def __init__(self, message=None):
        self.message = message
