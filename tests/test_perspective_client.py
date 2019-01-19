import pytest
import requests_mock

from chtools.perspective.client import PerspectiveClient


def test_create():
    client = PerspectiveClient('fake_api_key')

    # create will check if perspective with same name exists. So need to mock
    # index as well.
    index_mock_response = {
        '2954937501756': {
            'name': 'BCT - Accounts by Billing Account', 'active': True
        },
        '343598849467': {
            'name': 'BCT Customers', 'active': True
        }
    }

    create_mock_response = {'message': 'Perspective 2954937502939 created'}

    # create will retrieve the schema for the new perspective
    get_schema_response = {
        'schema': {'name': 'tag_filter', 'include_in_reports': 'true',
                   'rules': [], 'merges': [], 'constants': [
                {'type': 'Static Group', 'list': [
                    {'ref_id': '2954937634073', 'name': 'Other',
                     'is_other': 'true'}]}]}}

    with requests_mock.Mocker() as m:
        m.get('https://chapi.cloudhealthtech.com/v1/perspective_schemas/',
              json=index_mock_response)
        m.post('https://chapi.cloudhealthtech.com/v1/perspective_schemas',
               json=create_mock_response)
        m.get('https://chapi.cloudhealthtech.com/v1/perspective_schemas/2954937502939',
              json=get_schema_response)
        # Returns a Perspective object
        perspective = client.create('tag_filter')

    assert perspective.id == '2954937502939'


def test_delete():
    client = PerspectiveClient('fake_api_key')

    index_mock_response = {
        '2954937501756': {
            'name': 'BCT - Accounts by Billing Account', 'active': True
        },
        '343598849467': {
            'name': 'BCT Customers', 'active': True
        },
        '2954937502942': {
            'name': 'tag_filter', 'active': True
        }
    }

    get_schema_mock_response = {
        'schema': {'name': 'tag_filter', 'include_in_reports': 'true',
                   'rules': [{'type': 'filter', 'asset': 'AwsAsset',
                              'to': '2954937634084', 'condition': {'clauses': [
                           {'tag_field': ['Env'], 'op': '=', 'val': 'Dev'}]}},
                             {'type': 'filter', 'asset': 'AwsAsset',
                              'to': '2954937634085', 'condition': {'clauses': [
                                 {'tag_field': ['Env'], 'op': '=',
                                  'val': 'Stage'}]}},
                             {'type': 'filter', 'asset': 'AwsAsset',
                              'to': '2954937634086', 'condition': {'clauses': [
                                 {'tag_field': ['Env'], 'op': '=',
                                  'val': 'Prod'}]}}], 'merges': [],
                   'constants': [{'type': 'Static Group', 'list': [
                       {'ref_id': '2954937634084', 'name': 'Dev'},
                       {'ref_id': '2954937634085', 'name': 'Stage'},
                       {'ref_id': '2954937634086', 'name': 'Prod'},
                       {'ref_id': '2954937634083', 'name': 'Other',
                        'is_other': 'true'}]}]}}

    rename_perspective_mock_response = {
        'message': 'Perspective 2954937502942 updated'
    }

    delete_perspective_mock_response = {
        'message': 'Perspective [2954937502942] deleted.'
    }

    with requests_mock.Mocker() as m:
        m.get('https://chapi.cloudhealthtech.com/v1/perspective_schemas/',
              json=index_mock_response)
        m.get('https://chapi.cloudhealthtech.com/v1/perspective_schemas/2954937502942',
              json=get_schema_mock_response)
        m.put('https://chapi.cloudhealthtech.com/v1/perspective_schemas/2954937502942',
              json=rename_perspective_mock_response)
        m.delete('https://chapi.cloudhealthtech.com/v1/perspective_schemas/2954937502942',
                 json=delete_perspective_mock_response)
        # Returns a Perspective object
        result = client.delete('tag_filter')

    assert result._schema is None


def test_get():
    client = PerspectiveClient('fake_api_key')

    index_mock_response = {
        '2954937501756': {
            'name': 'BCT - Accounts by Billing Account', 'active': True
        },
        '343598849467': {
            'name': 'BCT Customers', 'active': True
        },
        '2954937502943': {
            'name': 'tag_filter', 'active': True
        }
    }

    get_schema_mock_response = {
        'schema': {'name': 'tag_filter', 'include_in_reports': 'true',
                   'rules': [{'type': 'filter', 'asset': 'AwsAsset',
                              'to': '2954937634084', 'condition': {'clauses': [
                           {'tag_field': ['Env'], 'op': '=', 'val': 'Dev'}]}},
                             {'type': 'filter', 'asset': 'AwsAsset',
                              'to': '2954937634085', 'condition': {'clauses': [
                                 {'tag_field': ['Env'], 'op': '=',
                                  'val': 'Stage'}]}},
                             {'type': 'filter', 'asset': 'AwsAsset',
                              'to': '2954937634086', 'condition': {'clauses': [
                                 {'tag_field': ['Env'], 'op': '=',
                                  'val': 'Prod'}]}}], 'merges': [],
                   'constants': [{'type': 'Static Group', 'list': [
                       {'ref_id': '2954937634084', 'name': 'Dev'},
                       {'ref_id': '2954937634085', 'name': 'Stage'},
                       {'ref_id': '2954937634086', 'name': 'Prod'},
                       {'ref_id': '2954937634083', 'name': 'Other',
                        'is_other': 'true'}]}]}}

    with requests_mock.Mocker() as m:
        m.get('https://chapi.cloudhealthtech.com/v1/perspective_schemas/',
              json=index_mock_response)
        m.get('https://chapi.cloudhealthtech.com/v1/perspective_schemas/2954937502943',
              json=get_schema_mock_response)
        # Returns a Perspective object
        result = client.get('tag_filter')

    assert result.name == 'tag_filter'


def test_index():
    client = PerspectiveClient('fake_api_key')

    mock_response = {
        '2954937501756': {
            'name': 'BCT - Accounts by Billing Account', 'active': True
        },
        '343598849467': {
            'name': 'BCT Customers', 'active': True
        }
    }

    with requests_mock.Mocker() as m:
        m.get('https://chapi.cloudhealthtech.com/v1/perspective_schemas/',
              json=mock_response)
        result = client.index()

    assert result.get('2954937501756')


def test_update():
    client = PerspectiveClient('fake_api_key')

    index_mock_response = {
        '2954937501756': {
            'name': 'BCT - Accounts by Billing Account', 'active': True
        },
        '343598849467': {
            'name': 'BCT Customers', 'active': True
        },
        '2954937502943': {
            'name': 'tag_filter', 'active': True
        }
    }

    get_schema_mock_response_inital = {
        'schema': {'name': 'tag_filter', 'include_in_reports': 'true',
                   'rules': [{'type': 'filter', 'asset': 'AwsAsset',
                              'to': '2954937634084', 'condition': {'clauses': [
                           {'tag_field': ['Env'], 'op': '=', 'val': 'Dev'}]}},
                             {'type': 'filter', 'asset': 'AwsAsset',
                              'to': '2954937634085', 'condition': {'clauses': [
                                 {'tag_field': ['Env'], 'op': '=',
                                  'val': 'Stage'}]}},
                             {'type': 'filter', 'asset': 'AwsAsset',
                              'to': '2954937634086', 'condition': {'clauses': [
                                 {'tag_field': ['Env'], 'op': '=',
                                  'val': 'Prod'}]}}], 'merges': [],
                   'constants': [{'type': 'Static Group', 'list': [
                       {'ref_id': '2954937634084', 'name': 'Dev'},
                       {'ref_id': '2954937634085', 'name': 'Stage'},
                       {'ref_id': '2954937634086', 'name': 'Prod'},
                       {'ref_id': '2954937634083', 'name': 'Other',
                        'is_other': 'true'}]}]}}

    update_schema_mock_response = {
        'message': 'Perspective 2954937502943 updated'
    }

    get_schema_mock_response_updated = {
        'schema': {'name': 'tag_filter', 'include_in_reports': 'true',
                   'rules': [{'type': 'filter', 'asset': 'AwsAsset',
                              'to': '2954937634088',
                              'condition': {'combine_with': 'OR', 'clauses': [
                                  {'tag_field': ['Env'], 'op': '=',
                                   'val': 'Dev'},
                                  {'tag_field': ['Env'], 'op': '=',
                                   'val': 'Test'}]}},
                             {'type': 'filter', 'asset': 'AwsAsset',
                              'to': '2954937634089', 'condition': {'clauses': [
                                 {'tag_field': ['Env'], 'op': '=',
                                  'val': 'Stage'}]}},
                             {'type': 'filter', 'asset': 'AwsAsset',
                              'to': '2954937634090', 'condition': {'clauses': [
                                 {'tag_field': ['Env'], 'op': '=',
                                  'val': 'Prod'}]}},
                             {'type': 'filter', 'asset': 'AwsAsset',
                              'to': '2954937634091', 'condition': {'clauses': [
                                 {'tag_field': ['Env'], 'op': '=',
                                  'val': 'DR'}]}}], 'merges': [],
                   'constants': [{'type': 'Static Group', 'list': [
                       {'ref_id': '2954937634088', 'name': 'Dev'},
                       {'ref_id': '2954937634089', 'name': 'Stage'},
                       {'ref_id': '2954937634090', 'name': 'Prod'},
                       {'ref_id': '2954937634091', 'name': 'DR'},
                       {'ref_id': '2954937634087', 'name': 'Other',
                        'is_other': 'true'}]}]}}

    with requests_mock.Mocker() as m:
        m.get('https://chapi.cloudhealthtech.com/v1/perspective_schemas/',
              json=index_mock_response)
        m.put('https://chapi.cloudhealthtech.com/v1/perspective_schemas/2954937502943',
               json=update_schema_mock_response)
        m.register_uri(
            'GET',
            'https://chapi.cloudhealthtech.com/v1/perspective_schemas/2954937502943',
            [
                {'json': get_schema_mock_response_inital,
                 'status_code': 200},
                {'json': get_schema_mock_response_updated,
                 'status_code': 200}
            ]
        )
        # Returns a Perspective object
        perspective = client.update('tag_filter',
                                    schema=get_schema_mock_response_updated['schema'])

    rules = perspective.schema['rules']

    assert len(rules) == 4


def test_update_mismatch_name():
    client = PerspectiveClient('fake_api_key')

    index_mock_response = {
        '2954937501756': {
            'name': 'BCT - Accounts by Billing Account', 'active': True
        },
        '343598849467': {
            'name': 'BCT Customers', 'active': True
        },
        '2954937502943': {
            'name': 'tag_filter', 'active': True
        }
    }

    get_schema_mock_response_inital = {
        'schema': {'name': 'tag_filter', 'include_in_reports': 'true',
                   'rules': [{'type': 'filter', 'asset': 'AwsAsset',
                              'to': '2954937634084', 'condition': {'clauses': [
                           {'tag_field': ['Env'], 'op': '=', 'val': 'Dev'}]}},
                             {'type': 'filter', 'asset': 'AwsAsset',
                              'to': '2954937634085', 'condition': {'clauses': [
                                 {'tag_field': ['Env'], 'op': '=',
                                  'val': 'Stage'}]}},
                             {'type': 'filter', 'asset': 'AwsAsset',
                              'to': '2954937634086', 'condition': {'clauses': [
                                 {'tag_field': ['Env'], 'op': '=',
                                  'val': 'Prod'}]}}], 'merges': [],
                   'constants': [{'type': 'Static Group', 'list': [
                       {'ref_id': '2954937634084', 'name': 'Dev'},
                       {'ref_id': '2954937634085', 'name': 'Stage'},
                       {'ref_id': '2954937634086', 'name': 'Prod'},
                       {'ref_id': '2954937634083', 'name': 'Other',
                        'is_other': 'true'}]}]}}

    updated_schema = {
                'name': 'empty_schema',
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

    with requests_mock.Mocker() as m:
        m.get('https://chapi.cloudhealthtech.com/v1/perspective_schemas/',
              json=index_mock_response)
        m.get('https://chapi.cloudhealthtech.com/v1/perspective_schemas/2954937502943',
              json=get_schema_mock_response_inital)
        with pytest.raises(ValueError) as e:
            client.update('tag_filter', schema=updated_schema)
        assert str(e.value) == "perspective_name empty_schema does not match name tag_filter in provided schema or spec"


