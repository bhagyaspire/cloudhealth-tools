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

    create_mock_respone = {'message': 'Perspective 2954937502939 created'}

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
               json=create_mock_respone)
        m.get('https://chapi.cloudhealthtech.com/v1/perspective_schemas/2954937502939',
              json=get_schema_response)
        # Returns a Perspective object
        perspective = client.create('tag_filter')

    assert perspective.id == '2954937502939'


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



