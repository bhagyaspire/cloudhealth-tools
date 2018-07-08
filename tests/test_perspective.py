import logging

from deepdiff import DeepDiff
import pytest
import yaml

from cloudhealth.perspective import Perspective

logger = logging.getLogger('cloudhealth.perspective')
logger.setLevel(logging.DEBUG)


@pytest.fixture()
def search_spec():
    with open('tests/specs/search-perspective.yaml') as spec_file:
        spec = yaml.load(spec_file)
    return spec


@pytest.fixture()
def group_by_tag_value_spec():
    with open('tests/specs/autogroup.yaml') as spec_file:
        spec = yaml.load(spec_file)
    return spec


@pytest.fixture()
def categorize_perspective():
    with open('tests/specs/categorize-perspective.yaml') as spec_file:
        spec = yaml.load(spec_file)
    return spec


@pytest.fixture()
def new_perspective():
    http_client = None
    perspective = Perspective(http_client)
    empty_schema = {
                        'name': 'new_perspective',
                        'merges': [],
                        'constants': [{
                            'list': [{
                                'name': 'Other',
                                'ref_id': '1234567890',
                                'is_other': 'true'
                            }],
                            'type': 'Static Group'
                        }],
                        'include_in_reports': 'true',
                        'rules': []
                    }
    perspective._schema = empty_schema
    return perspective


def test_create_search_perspective(new_perspective, search_spec):
    perspective = new_perspective
    perspective.update_spec(search_spec)

    expected_schema = {
        'constants': [{'list': [{'is_other': 'true',
                                  'name': 'Other',
                                  'ref_id': '1234567890'},
                                 {'name': 'Admin', 'ref_id': 101},
                                 {'name': 'Other', 'ref_id': 102},
                                 {'name': 'Web', 'ref_id': 103},
                                 {'name': 'Non-Conforming', 'ref_id': 104}],
                        'type': 'Static Group'}],
         'include_in_reports': True,
         'merges': [],
         'name': 'Service',
         'rules': [{'asset': 'AwsAsset',
                    'condition': {'clauses': [{'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'Admin'}]},
                    'to': 101,
                    'type': 'filter'},
                   {'asset': 'AwsTaggableAsset',
                    'condition': {'clauses': [{'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'Admin'}]},
                    'to': 101,
                    'type': 'filter'},
                   {'asset': 'AwsEmrCluster',
                    'condition': {'clauses': [{'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'Admin'}]},
                    'to': 101,
                    'type': 'filter'},
                   {'asset': 'AwsAsset',
                    'condition': {'clauses': [{'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'other'},
                                              {'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'Other'}],
                                  'combine_with': 'OR'},
                    'to': 102,
                    'type': 'filter'},
                   {'asset': 'AwsTaggableAsset',
                    'condition': {'clauses': [{'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'other'},
                                              {'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'Other'}],
                                  'combine_with': 'OR'},
                    'to': 102,
                    'type': 'filter'},
                   {'asset': 'AwsEmrCluster',
                    'condition': {'clauses': [{'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'other'},
                                              {'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'Other'}],
                                  'combine_with': 'OR'},
                    'to': 102,
                    'type': 'filter'},
                   {'asset': 'AwsAsset',
                    'condition': {'clauses': [{'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'Web'},
                                              {'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'WWW'}],
                                  'combine_with': 'OR'},
                    'to': 103,
                    'type': 'filter'},
                   {'asset': 'AwsAsset',
                    'condition': {'clauses': [{'op': '=',
                                               'tag_field': ['Tier'],
                                               'val': 'Web'},
                                              {'op': '=',
                                               'tag_field': ['Tier'],
                                               'val': 'WWW'}],
                                  'combine_with': 'OR'},
                    'to': 103,
                    'type': 'filter'},
                   {'asset': 'AwsTaggableAsset',
                    'condition': {'clauses': [{'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'Web'},
                                              {'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'WWW'}],
                                  'combine_with': 'OR'},
                    'to': 103,
                    'type': 'filter'},
                   {'asset': 'AwsTaggableAsset',
                    'condition': {'clauses': [{'op': '=',
                                               'tag_field': ['Tier'],
                                               'val': 'Web'},
                                              {'op': '=',
                                               'tag_field': ['Tier'],
                                               'val': 'WWW'}],
                                  'combine_with': 'OR'},
                    'to': 103,
                    'type': 'filter'},
                   {'asset': 'AwsEmrCluster',
                    'condition': {'clauses': [{'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'Web'},
                                              {'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'WWW'}],
                                  'combine_with': 'OR'},
                    'to': 103,
                    'type': 'filter'},
                   {'asset': 'AwsEmrCluster',
                    'condition': {'clauses': [{'op': '=',
                                               'tag_field': ['Tier'],
                                               'val': 'Web'},
                                              {'op': '=',
                                               'tag_field': ['Tier'],
                                               'val': 'WWW'}],
                                  'combine_with': 'OR'},
                    'to': 103,
                    'type': 'filter'},
                   {'asset': 'AwsAsset',
                    'condition': {'clauses': [{'op': 'Has A Value',
                                               'tag_field': ['Service']}]},
                    'to': 104,
                    'type': 'filter'},
                   {'asset': 'AwsTaggableAsset',
                    'condition': {'clauses': [{'op': 'Has A Value',
                                               'tag_field': ['Service']}]},
                    'to': 104,
                    'type': 'filter'},
                   {'asset': 'AwsEmrCluster',
                    'condition': {'clauses': [{'op': 'Has A Value',
                                               'tag_field': ['Service']}]},
                    'to': 104,
                    'type': 'filter'}]}

    differences = DeepDiff(expected_schema, perspective.schema)
    assert differences == {}, (
        "DeepDiff reports the following differences between expected schema "
        "and generated schema: {}".format(differences)
    )


def test_create_group_by_tag_value_perspective(new_perspective,
                                               group_by_tag_value_spec):
    perspective = new_perspective
    perspective.update_spec(group_by_tag_value_spec)

    expected_schema = {
        'constants': [{'list': [{'is_other': 'true',
                          'name': 'Other',
                          'ref_id': '1234567890'},
                         {'name': 'Web', 'ref_id': 101},
                         {'name': 'App', 'ref_id': 102},
                         {'name': 'DB', 'ref_id': 103},
                         {'name': 'Non-Conforming', 'ref_id': 104}],
                'type': 'Static Group'}],
         'include_in_reports': 'true',
         'merges': [],
         'name': 'ServiceAutoGroup',
         'rules': [{'asset': 'AwsAsset',
                    'condition': {'clauses': [{'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'Web'}]},
                    'to': 101,
                    'type': 'filter'},
                   {'asset': 'AwsTaggableAsset',
                    'condition': {'clauses': [{'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'Web'}]},
                    'to': 101,
                    'type': 'filter'},
                   {'asset': 'AwsEmrCluster',
                    'condition': {'clauses': [{'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'Web'}]},
                    'to': 101,
                    'type': 'filter'},
                   {'asset': 'AwsAsset',
                    'condition': {'clauses': [{'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'App'}]},
                    'to': 102,
                    'type': 'filter'},
                   {'asset': 'AwsTaggableAsset',
                    'condition': {'clauses': [{'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'App'}]},
                    'to': 102,
                    'type': 'filter'},
                   {'asset': 'AwsEmrCluster',
                    'condition': {'clauses': [{'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'App'}]},
                    'to': 102,
                    'type': 'filter'},
                   {'asset': 'AwsAsset',
                    'condition': {'clauses': [{'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'DB'}]},
                    'to': 103,
                    'type': 'filter'},
                   {'asset': 'AwsTaggableAsset',
                    'condition': {'clauses': [{'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'DB'}]},
                    'to': 103,
                    'type': 'filter'},
                   {'asset': 'AwsEmrCluster',
                    'condition': {'clauses': [{'op': '=',
                                               'tag_field': ['Service'],
                                               'val': 'DB'}]},
                    'to': 103,
                    'type': 'filter'},
                   {'asset': 'AwsAsset',
                    'condition': {'clauses': [{'op': 'Has A Value',
                                               'tag_field': ['Service']}]},
                    'to': 104,
                    'type': 'filter'},
                   {'asset': 'AwsTaggableAsset',
                    'condition': {'clauses': [{'op': 'Has A Value',
                                               'tag_field': ['Service']}]},
                    'to': 104,
                    'type': 'filter'},
                   {'asset': 'AwsEmrCluster',
                    'condition': {'clauses': [{'op': 'Has A Value',
                                               'tag_field': ['Service']}]},
                    'to': 104,
                    'type': 'filter'}]}

    differences = DeepDiff(expected_schema, perspective.schema)
    assert differences == {}, (
        "DeepDiff reports the following differences between expected schema "
        "and generated schema: {}".format(differences)
    )


def test_create_categorize_perspective(new_perspective,
                                       categorize_perspective):
    perspective = new_perspective
    perspective.update_spec(categorize_perspective)

    expected_schema = {
                        'constants': [{'list': [{'is_other': 'true',
                                          'name': 'Other',
                                          'ref_id': '1234567890'}],
                                'type': 'Static Group'},
                               {'list': [{'name': 'Creator', 'ref_id': 101}],
                                'type': 'Dynamic Group Block'},
                               {'list': [{'blk_id': 101,
                                          'name': 'placeholder',
                                          'ref_id': '123456',
                                          'val': 'placeholder'}],
                                'type': 'Dynamic Group'}],
                         'include_in_reports': 'true',
                         'merges': [],
                         'name': 'DynamicOwner',
                         'rules': [{'asset': 'AwsTaggableAsset',
                                    'name': 'Creator',
                                    'ref_id': 101,
                                    'tag_field': ['Creator'],
                                    'type': 'categorize'}]}

    differences = DeepDiff(expected_schema, perspective.schema)
    assert differences == {}, (
        "DeepDiff reports the following differences between expected schema "
        "and generated schema: {}".format(differences)
    )
