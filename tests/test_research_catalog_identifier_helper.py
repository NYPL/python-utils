import pytest
import json

from nypl_py_utils.functions.research_catalog_identifier_helper import (
    parse_research_catalog_identifier, research_catalog_id_prefix,
    ResearchCatalogIdentifierError)

_TEST_MAPPING = {
  'sierra-nypl': {
    'organization': 'nyplOrg:0001',
    'bibPrefix': 'b',
    'holdingPrefix': 'h',
    'itemPrefix': 'i'
  },
  'recap-pul': {
    'organization': 'nyplOrg:0003',
    'bibPrefix': 'pb',
    'itemPrefix': 'pi'
  },
  'recap-cul': {
    'organization': 'nyplOrg:0002',
    'bibPrefix': 'cb',
    'itemPrefix': 'ci'
  },
  'recap-hl': {
    'organization': 'nyplOrg:0004',
    'bibPrefix': 'hb',
    'itemPrefix': 'hi'
  }
}


class TestResearchCatalogIdentifierHelper:
    @pytest.fixture(autouse=True)
    def test_instance(self, requests_mock):
        requests_mock.get(
            'https://raw.githubusercontent.com/NYPL/nypl-core/master/mappings/recap-discovery/nypl-source-mapping.json', # noqa
            text=json.dumps(_TEST_MAPPING))

    def test_parse_research_catalog_identifier_parses_valid(self):
        assert parse_research_catalog_identifier('b1234') == \
                {'id': '1234', 'nyplSource': 'sierra-nypl', 'nyplType': 'bib'}
        assert parse_research_catalog_identifier('cb1234') == \
               {'id': '1234', 'nyplSource': 'recap-cul', 'nyplType': 'bib'}
        assert parse_research_catalog_identifier('pi1234') == \
               {'id': '1234', 'nyplSource': 'recap-pul', 'nyplType': 'item'}
        assert parse_research_catalog_identifier('h1234') == \
               {'id': '1234', 'nyplSource': 'sierra-nypl',
                      'nyplType': 'holding'}

    def test_parse_research_catalog_identifier_fails_nonsense(self):
        for invalidIdentifier in [None, 1234, 'z1234', '1234']:
            with pytest.raises(ResearchCatalogIdentifierError):
                parse_research_catalog_identifier(invalidIdentifier)

    def test_research_catalog_id_prefix_parses_valid(self, mocker):
        assert research_catalog_id_prefix('sierra-nypl') == 'b'
        assert research_catalog_id_prefix('sierra-nypl', 'bib') == 'b'
        assert research_catalog_id_prefix('sierra-nypl', 'item') == 'i'
        assert research_catalog_id_prefix('sierra-nypl', 'holding') == 'h'
        assert research_catalog_id_prefix('recap-pul', 'bib') == 'pb'
        assert research_catalog_id_prefix('recap-hl', 'bib') == 'hb'
        assert research_catalog_id_prefix('recap-hl', 'item') == 'hi'
        assert research_catalog_id_prefix('recap-pul', 'item') == 'pi'

    def test_research_catalog_id_prefix_fails_nonsense(self, mocker):
        for invalidSource in ['sierra-cul', None, 'recap-nypl']:
            with pytest.raises(ResearchCatalogIdentifierError):
                research_catalog_id_prefix(invalidSource)
        for invalidType in [None, '...']:
            with pytest.raises(ResearchCatalogIdentifierError):
                research_catalog_id_prefix('sierra-nypl', invalidType)
