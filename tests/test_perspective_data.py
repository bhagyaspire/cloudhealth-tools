import json
import logging
import os

import pytest
import yaml
from deepdiff import DeepDiff

from chtools.perspective.data import Perspective

logger = logging.getLogger('chtools.perspective')
logger.setLevel(logging.DEBUG)

path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)
specs_dir = dir_path + "/perspective_data/specs"
schemas_dir = dir_path + "/perspective_data/schemas"

# general_test_cases are for test cases to convert both ways between
# schema and spec
general_test_cases = [
        'tag_filter',
        'tag_search',
        'tag_active',
        'multiple_rules_to_a_group',
        'categorize',
        'categorize_and_filters',
        'tag_filter_multiple_assets'
    ]

spec_to_schema_test_cases = ['tag_filter_match_lowercase']
schema_to_spec_test_cases = ['categorize_with_merges']


@pytest.mark.parametrize(
    'test_case', general_test_cases + spec_to_schema_test_cases

)
def test_spec_to_schema(test_case):
    perspective = Perspective(http_client=None)
    spec_path = '{}/{}.yaml'.format(specs_dir, test_case)
    with open(spec_path) as spec_file:
        spec = yaml.load(spec_file)
    schema_path = '{}/{}.json'.format(schemas_dir, test_case)
    with open(schema_path) as schema_file:
        expected_schema = json.load(schema_file)
    perspective.spec = spec
    differences = DeepDiff(expected_schema, perspective.schema)
    assert differences == {}, (
        "DeepDiff reports the following differences between expected schema "
        "and generated schema: {}".format(differences)
    )


@pytest.mark.parametrize(
    'test_case', general_test_cases + schema_to_spec_test_cases

)
def test_schema_to_spec(test_case):
    perspective = Perspective(http_client=None)
    spec_path = '{}/{}.yaml'.format(specs_dir, test_case)
    with open(spec_path) as spec_file:
        expected_spec = yaml.load(spec_file)
    schema_path = '{}/{}.json'.format(schemas_dir, test_case)
    with open(schema_path) as schema_file:
        schema = json.load(schema_file)
    perspective.schema = schema
    differences = DeepDiff(expected_spec, yaml.load(perspective.spec))
    # Support difference of 'search' type becoming 'filter' type
    if differences.get('values_changed'):
        diff_keys_to_remove = []
        for key, value in differences['values_changed'].items():
            if (value['new_value'] == 'filter'
                    and value['old_value'] == 'search'):
                diff_keys_to_remove.append(key)
        for key in diff_keys_to_remove:
            del differences['values_changed'][key]
        if differences == {'values_changed': {}}:
            del differences['values_changed']

    assert differences == {}, (
        "DeepDiff reports the following differences between expected schema "
        "and generated schema: {}".format(differences)
    )


def test_update_filter_via_spec():
    perspective = Perspective(http_client=None)
    initial_schema_path = '{}/tag_filter.json'.format(schemas_dir)
    with open(initial_schema_path) as initial_schema_path:
        perspective.schema = json.load(initial_schema_path)
    update_spec_path = '{}/tag_filter_update.yaml'.format(specs_dir)
    with open(update_spec_path) as update_spec_file:
        perspective.spec = yaml.load(update_spec_file)
    expected_schema_path = '{}/tag_filter_update.json'.format(schemas_dir)
    with open(expected_schema_path) as expected_schema_file:
        expected_schema = json.load(expected_schema_file)

    differences = DeepDiff(expected_schema, perspective.schema)
    assert differences == {}, (
        "DeepDiff reports the following differences between expected schema "
        "and generated schema: {}".format(differences)
    )


def test_add_categorize_via_spec():
    perspective = Perspective(http_client=None)
    initial_schema_path = '{}/tag_filter.json'.format(schemas_dir)
    with open(initial_schema_path) as initial_schema_path:
        perspective.schema = json.load(initial_schema_path)
    update_spec_path = '{}/tag_filter_add_categorize.yaml'.format(specs_dir)
    with open(update_spec_path) as update_spec_file:
        perspective.spec = yaml.load(update_spec_file)
    expected_schema_path = '{}/tag_filter_add_categorize.json'.format(
        schemas_dir
    )
    with open(expected_schema_path) as expected_schema_file:
        expected_schema = json.load(expected_schema_file)

    differences = DeepDiff(expected_schema, perspective.schema)
    assert differences == {}, (
        "DeepDiff reports the following differences between expected schema "
        "and generated schema: {}".format(differences)
    )


def test_categorize_group_merge():
    perspective = Perspective(None)
    perspective.id = '2954937503983'
    # set initial schema
    perspective.schema = {'name': 'Environments', 'include_in_reports': 'true',
                          'rules': [{'type': 'categorize', 'asset': 'AwsAsset',
                                     'tag_field': ['Environment'],
                                     'ref_id': '2954937505877',
                                     'name': 'Environments'}], 'merges': [],
                          'constants': [{'type': 'Dynamic Group Block',
                                         'list': [{'ref_id': '2954937505877',
                                                   'name': 'Environments'}]},
                                        {'type': 'Dynamic Group', 'list': [
                                            {'ref_id': '2954937647846',
                                             'blk_id': '2954937505877',
                                             'val': 'Development',
                                             'name': 'Development'},
                                            {'ref_id': '2954937647847',
                                             'blk_id': '2954937505877',
                                             'val': 'Live', 'name': 'Live'},
                                            {'ref_id': '2954937647850',
                                             'blk_id': '2954937505877',
                                             'val': 'Production',
                                             'name': 'Production'},
                                            {'ref_id': '2954937647851',
                                             'blk_id': '2954937505877',
                                             'val': 'Integration Testing',
                                             'name': 'Integration Testing'},
                                            {'ref_id': '2954937647853',
                                             'blk_id': '2954937505877',
                                             'val': 'live', 'name': 'live'}]},
                                        {'type': 'Static Group', 'list': [
                                            {'ref_id': '2954937647845',
                                             'name': 'Other',
                                             'is_other': 'true'}]}]}
    # Apply spec with merges
    perspective.spec = {'include_in_reports': 'true', 'merges': [
        {'from': ['Live', 'live'], 'name': 'Environments', 'to': 'Production',
         'type': 'Group'}], 'name': 'Environments', 'rules': [
        {'asset': 'AwsAsset', 'name': 'Environments',
         'tag_field': 'Environment', 'to': 'Environments',
         'type': 'categorize'}]}

    expected_schema = {'name': 'Environments', 'include_in_reports': 'true',
                       'rules': [{'asset': 'AwsAsset', 'name': 'Environments',
                                  'tag_field': ['Environment'],
                                  'type': 'categorize',
                                  'ref_id': '2954937505877'}], 'merges': [
            {'type': 'Group', 'to': '2954937647850',
             'from': ['2954937647847', '2954937647853']}], 'constants': [
            {'type': 'Dynamic Group Block',
             'list': [{'ref_id': '2954937505877', 'name': 'Environments'}]},
            {'type': 'Dynamic Group', 'list': [
                {'ref_id': '2954937647846', 'blk_id': '2954937505877',
                 'val': 'Development', 'name': 'Development'},
                {'ref_id': '2954937647847', 'blk_id': '2954937505877',
                 'val': 'Live', 'name': 'Live', 'fwd_to': '2954937647850'},
                {'ref_id': '2954937647850', 'blk_id': '2954937505877',
                 'val': 'Production', 'name': 'Production'},
                {'ref_id': '2954937647851', 'blk_id': '2954937505877',
                 'val': 'Integration Testing', 'name': 'Integration Testing'},
                {'ref_id': '2954937647853', 'blk_id': '2954937505877',
                 'val': 'live', 'name': 'live', 'fwd_to': '2954937647850'}]},
            {'type': 'Static Group', 'list': [
                {'ref_id': '2954937647845', 'name': 'Other',
                 'is_other': 'true'}]}]}

    differences = DeepDiff(expected_schema, perspective.schema)
    assert differences == {}, (
        "DeepDiff reports the following differences between expected schema "
        "and generated schema: {}".format(differences)
    )


def test_categorize_group_merge_from_regex():
    perspective = Perspective(None)
    perspective.id = '2954937503995'
    # set initial schema
    perspective.schema = {'name': 'EnvironmentsTest',
                          'include_in_reports': 'true', 'rules': [
            {'type': 'categorize', 'asset': 'AwsAsset',
             'tag_field': ['Environment'], 'ref_id': '2954937505889',
             'name': 'Environments'}], 'merges': [], 'constants': [
            {'type': 'Dynamic Group Block',
             'list': [{'ref_id': '2954937505889', 'name': 'Environments'}]},
            {'type': 'Dynamic Group', 'list': [
                {'ref_id': '2954937648352', 'blk_id': '2954937505889',
                 'val': 'Development', 'name': 'Development'},
                {'ref_id': '2954937648353', 'blk_id': '2954937505889',
                 'val': 'Live', 'name': 'Live'},
                {'ref_id': '2954937648354', 'blk_id': '2954937505889',
                 'val': 'staging', 'name': 'staging'},
                {'ref_id': '2954937648355', 'blk_id': '2954937505889',
                 'val': 'Sandbox', 'name': 'Sandbox'},
                {'ref_id': '2954937648356', 'blk_id': '2954937505889',
                 'val': 'Production', 'name': 'Production'},
                {'ref_id': '2954937648357', 'blk_id': '2954937505889',
                 'val': 'Integration Testing', 'name': 'Integration Testing'},
                {'ref_id': '2954937648358', 'blk_id': '2954937505889',
                 'val': 'Other', 'name': 'Other'},
                {'ref_id': '2954937648359', 'blk_id': '2954937505889',
                 'val': 'live', 'name': 'live'},
                {'ref_id': '2954937648360', 'blk_id': '2954937505889',
                 'val': 'Staging', 'name': 'Staging'},
                {'ref_id': '2954937648361', 'blk_id': '2954937505889',
                 'val': 'Dev', 'name': 'Dev'},
                {'ref_id': '2954937648362', 'blk_id': '2954937505889',
                 'val': 'development', 'name': 'development'},
                {'ref_id': '2954937648363', 'blk_id': '2954937505889',
                 'val': 'Research', 'name': 'Research'},
                {'ref_id': '2954937648364', 'blk_id': '2954937505889',
                 'val': 'Discovery', 'name': 'Discovery'},
                {'ref_id': '2954937648365', 'blk_id': '2954937505889',
                 'val': 'tech', 'name': 'tech'},
                {'ref_id': '2954937648366', 'blk_id': '2954937505889',
                 'val': 'ci', 'name': 'ci'},
                {'ref_id': '2954937648367', 'blk_id': '2954937505889',
                 'val': 'QA', 'name': 'QA'},
                {'ref_id': '2954937648368', 'blk_id': '2954937505889',
                 'val': 'production', 'name': 'production'},
                {'ref_id': '2954937648369', 'blk_id': '2954937505889',
                 'val': 'Integration', 'name': 'Integration'},
                {'ref_id': '2954937648370', 'blk_id': '2954937505889',
                 'val': 'integration', 'name': 'integration'},
                {'ref_id': '2954937648371', 'blk_id': '2954937505889',
                 'val': 'Tech', 'name': 'Tech'},
                {'ref_id': '2954937648372', 'blk_id': '2954937505889',
                 'val': 'sandbox', 'name': 'sandbox'},
                {'ref_id': '2954937648373', 'blk_id': '2954937505889',
                 'val': 'QC', 'name': 'QC'},
                {'ref_id': '2954937648374', 'blk_id': '2954937505889',
                 'val': 'dev', 'name': 'dev'},
                {'ref_id': '2954937648375', 'blk_id': '2954937505889',
                 'val': 'loadtest', 'name': 'loadtest'},
                {'ref_id': '2954937648376', 'blk_id': '2954937505889',
                 'val': 'qa', 'name': 'qa'},
                {'ref_id': '2954937648377', 'blk_id': '2954937505889',
                 'val': 'Image-Production', 'name': 'Image-Production'},
                {'ref_id': '2954937648378', 'blk_id': '2954937505889',
                 'val': 'Load Testing', 'name': 'Load Testing'},
                {'ref_id': '2954937648379', 'blk_id': '2954937505889',
                 'val': 'bko-backoffice', 'name': 'bko-backoffice'},
                {'ref_id': '2954937648380', 'blk_id': '2954937505889',
                 'val': 'cg-admin-platform-126',
                 'name': 'cg-admin-platform-126'},
                {'ref_id': '2954937648381', 'blk_id': '2954937505889',
                 'val': 'test', 'name': 'test'},
                {'ref_id': '2954937648382', 'blk_id': '2954937505889',
                 'val': 'Image-Development', 'name': 'Image-Development'},
                {'ref_id': '2954937648383', 'blk_id': '2954937505889',
                 'val': 'System', 'name': 'System'},
                {'ref_id': '2954937648384', 'blk_id': '2954937505889',
                 'val': 'demo', 'name': 'demo'},
                {'ref_id': '2954937648385', 'blk_id': '2954937505889',
                 'val': 'local', 'name': 'local'},
                {'ref_id': '2954937648386', 'blk_id': '2954937505889',
                 'val': 'Dataeng-Dev', 'name': 'Dataeng-Dev'},
                {'ref_id': '2954937648387', 'blk_id': '2954937505889',
                 'val': 'Dataeng-Prod', 'name': 'Dataeng-Prod'},
                {'ref_id': '2954937648388', 'blk_id': '2954937505889',
                 'val': 'a', 'name': 'a'},
                {'ref_id': '2954937648389', 'blk_id': '2954937505889',
                 'val': 'it', 'name': 'it'},
                {'ref_id': '2954937648390', 'blk_id': '2954937505889',
                 'val': 'BI', 'name': 'BI'},
                {'ref_id': '2954937648391', 'blk_id': '2954937505889',
                 'val': 'other', 'name': 'other'},
                {'ref_id': '2954937648392', 'blk_id': '2954937505889',
                 'val': 'live-qc', 'name': 'live-qc'}]},
            {'type': 'Static Group', 'list': [
                {'ref_id': '2954937648351', 'name': 'Other',
                 'is_other': 'true'}]}]}
    # Apply spec with merges
    perspective.spec = {'include_in_reports': 'true',
                        'name': 'EnvironmentsTest', 'rules': [
            {'asset': 'AwsAsset', 'name': 'Environments',
             'tag_field': 'Environment', 'to': 'Environments',
             'type': 'categorize'}], 'merges': [
            {'name': 'Environments', 'type': 'Group', 'to': 'Production',
             'from_regex': ['^[Ll]ive', '.*[Pp]rod.*', '^[Tt]ech$']},
            {'name': 'Environments', 'type': 'Group', 'to': 'Development',
             'from_regex': ['.*[Dd]ev.*', '^[Ss]andbox', '^Discovery$']}]}

    expected_schema = {'name': 'EnvironmentsTest',
                       'include_in_reports': 'true', 'rules': [
            {'type': 'categorize', 'asset': 'AwsAsset',
             'tag_field': ['Environment'], 'ref_id': '2954937505889',
             'name': 'Environments'}], 'merges': [
            {'type': 'Group', 'to': '2954937648356',
             'from': ['2954937648353', '2954937648359', '2954937648392',
                      '2954937648368', '2954937648377', '2954937648387',
                      '2954937648365', '2954937648371']},
            {'type': 'Group', 'to': '2954937648352',
             'from': ['2954937648361', '2954937648362', '2954937648374',
                      '2954937648382', '2954937648386', '2954937648355',
                      '2954937648372', '2954937648364']}], 'constants': [
            {'type': 'Dynamic Group Block',
             'list': [{'ref_id': '2954937505889', 'name': 'Environments'}]},
            {'type': 'Dynamic Group', 'list': [
                {'ref_id': '2954937648352', 'blk_id': '2954937505889',
                 'val': 'Development', 'name': 'Development'},
                {'ref_id': '2954937648353', 'blk_id': '2954937505889',
                 'val': 'Live', 'name': 'Live', 'fwd_to': '2954937648356'},
                {'ref_id': '2954937648354', 'blk_id': '2954937505889',
                 'val': 'staging', 'name': 'staging'},
                {'ref_id': '2954937648355', 'blk_id': '2954937505889',
                 'val': 'Sandbox', 'name': 'Sandbox',
                 'fwd_to': '2954937648352'},
                {'ref_id': '2954937648356', 'blk_id': '2954937505889',
                 'val': 'Production', 'name': 'Production'},
                {'ref_id': '2954937648357', 'blk_id': '2954937505889',
                 'val': 'Integration Testing', 'name': 'Integration Testing'},
                {'ref_id': '2954937648358', 'blk_id': '2954937505889',
                 'val': 'Other', 'name': 'Other'},
                {'ref_id': '2954937648359', 'blk_id': '2954937505889',
                 'val': 'live', 'name': 'live', 'fwd_to': '2954937648356'},
                {'ref_id': '2954937648360', 'blk_id': '2954937505889',
                 'val': 'Staging', 'name': 'Staging'},
                {'ref_id': '2954937648361', 'blk_id': '2954937505889',
                 'val': 'Dev', 'name': 'Dev', 'fwd_to': '2954937648352'},
                {'ref_id': '2954937648362', 'blk_id': '2954937505889',
                 'val': 'development', 'name': 'development',
                 'fwd_to': '2954937648352'},
                {'ref_id': '2954937648363', 'blk_id': '2954937505889',
                 'val': 'Research', 'name': 'Research'},
                {'ref_id': '2954937648364', 'blk_id': '2954937505889',
                 'val': 'Discovery', 'name': 'Discovery',
                 'fwd_to': '2954937648352'},
                {'ref_id': '2954937648365', 'blk_id': '2954937505889',
                 'val': 'tech', 'name': 'tech', 'fwd_to': '2954937648356'},
                {'ref_id': '2954937648366', 'blk_id': '2954937505889',
                 'val': 'ci', 'name': 'ci'},
                {'ref_id': '2954937648367', 'blk_id': '2954937505889',
                 'val': 'QA', 'name': 'QA'},
                {'ref_id': '2954937648368', 'blk_id': '2954937505889',
                 'val': 'production', 'name': 'production',
                 'fwd_to': '2954937648356'},
                {'ref_id': '2954937648369', 'blk_id': '2954937505889',
                 'val': 'Integration', 'name': 'Integration'},
                {'ref_id': '2954937648370', 'blk_id': '2954937505889',
                 'val': 'integration', 'name': 'integration'},
                {'ref_id': '2954937648371', 'blk_id': '2954937505889',
                 'val': 'Tech', 'name': 'Tech', 'fwd_to': '2954937648356'},
                {'ref_id': '2954937648372', 'blk_id': '2954937505889',
                 'val': 'sandbox', 'name': 'sandbox',
                 'fwd_to': '2954937648352'},
                {'ref_id': '2954937648373', 'blk_id': '2954937505889',
                 'val': 'QC', 'name': 'QC'},
                {'ref_id': '2954937648374', 'blk_id': '2954937505889',
                 'val': 'dev', 'name': 'dev', 'fwd_to': '2954937648352'},
                {'ref_id': '2954937648375', 'blk_id': '2954937505889',
                 'val': 'loadtest', 'name': 'loadtest'},
                {'ref_id': '2954937648376', 'blk_id': '2954937505889',
                 'val': 'qa', 'name': 'qa'},
                {'ref_id': '2954937648377', 'blk_id': '2954937505889',
                 'val': 'Image-Production', 'name': 'Image-Production',
                 'fwd_to': '2954937648356'},
                {'ref_id': '2954937648378', 'blk_id': '2954937505889',
                 'val': 'Load Testing', 'name': 'Load Testing'},
                {'ref_id': '2954937648379', 'blk_id': '2954937505889',
                 'val': 'bko-backoffice', 'name': 'bko-backoffice'},
                {'ref_id': '2954937648380', 'blk_id': '2954937505889',
                 'val': 'cg-admin-platform-126',
                 'name': 'cg-admin-platform-126'},
                {'ref_id': '2954937648381', 'blk_id': '2954937505889',
                 'val': 'test', 'name': 'test'},
                {'ref_id': '2954937648382', 'blk_id': '2954937505889',
                 'val': 'Image-Development', 'name': 'Image-Development',
                 'fwd_to': '2954937648352'},
                {'ref_id': '2954937648383', 'blk_id': '2954937505889',
                 'val': 'System', 'name': 'System'},
                {'ref_id': '2954937648384', 'blk_id': '2954937505889',
                 'val': 'demo', 'name': 'demo'},
                {'ref_id': '2954937648385', 'blk_id': '2954937505889',
                 'val': 'local', 'name': 'local'},
                {'ref_id': '2954937648386', 'blk_id': '2954937505889',
                 'val': 'Dataeng-Dev', 'name': 'Dataeng-Dev',
                 'fwd_to': '2954937648352'},
                {'ref_id': '2954937648387', 'blk_id': '2954937505889',
                 'val': 'Dataeng-Prod', 'name': 'Dataeng-Prod',
                 'fwd_to': '2954937648356'},
                {'ref_id': '2954937648388', 'blk_id': '2954937505889',
                 'val': 'a', 'name': 'a'},
                {'ref_id': '2954937648389', 'blk_id': '2954937505889',
                 'val': 'it', 'name': 'it'},
                {'ref_id': '2954937648390', 'blk_id': '2954937505889',
                 'val': 'BI', 'name': 'BI'},
                {'ref_id': '2954937648391', 'blk_id': '2954937505889',
                 'val': 'other', 'name': 'other'},
                {'ref_id': '2954937648392', 'blk_id': '2954937505889',
                 'val': 'live-qc', 'name': 'live-qc',
                 'fwd_to': '2954937648356'}]}, {'type': 'Static Group',
                                                'list': [
                                                    {'ref_id': '2954937648351',
                                                     'name': 'Other',
                                                     'is_other': 'true'}]}]}

    differences = DeepDiff(expected_schema, perspective.schema)
    assert differences == {}, (
        "DeepDiff reports the following differences between expected schema "
        "and generated schema: {}".format(differences)
    )
