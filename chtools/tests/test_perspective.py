import logging
import json
import os

import pytest
import yaml
from deepdiff import DeepDiff

from chtools.lib.perspective import Perspective

logger = logging.getLogger('cloudhealth.perspective')
logger.setLevel(logging.DEBUG)

path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)
specs_dir = dir_path + "/specs"
schemas_dir = dir_path + "/schemas"

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
schema_to_spec_test_cases = []


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