import requests_mock

import pytest

from chtools.aws_account.client import AwsAccountClient


@pytest.fixture()
def mock_schema_response():
    return {
        'id': 5909874999458, 
        'name': 'bcttest1',
        'amazon_name': 'bcttest1', 'owner_id': '619288149268',
        'hide_public_fields': False, 'region': 'global',
        'created_at': '2018-09-22T15:51:04Z',
        'updated_at': '2019-01-19T22:33:39Z',
        'account_type': 'Standalone', 'vpc_only': True,
        'cluster_name': 'bcttest1',
        'status': {'level': 'yellow',
                  'last_update': '2019-01-20T17:43:30Z'},
        'authentication': {
           'protocol': 'assume_role',
            'assume_role_arn': 'arn:aws:iam::619288149268:role/CloudHealth',
            'assume_role_external_id': '27beaf0b252df5700240e09ea7e96d'
        },
        'billing': {'is_consolidated': False},
        'cloudtrail': {'enabled': False}, 'ecs': {'enabled': False},
        'aws_config': {'enabled': False},
        'cloudwatch': {'enabled': True}, 'tags': [],
        'groups': [{'name': 'filter_test', 'group': 'Other'}],
        '_links': {
           'self': {'href': '/v1/aws_accounts/5909874999458'}}
    }


def test_create(mock_schema_response):
    client = AwsAccountClient('fake_api_key')

    mock_generated_external_id_response = {
        'generated_external_id': '27beaf0b252df5700240e09ea7e96d'
    }

    account_schema = {
        'name': 'bcttest1',
        'authentication': {
            'protocol': 'assume_role',
            'assume_role_arn': 'arn:aws:iam::619288149268:role/CloudHealth'
        },
        'billing': {
            "bucket": 'ch-dbr-bucket'
        }
        }

    with requests_mock.Mocker() as m:
        m.get(
            'https://chapi.cloudhealthtech.com/v1/aws_accounts/:id/generate_external_id',
            json=mock_generated_external_id_response
        )
        m.post(
            'https://chapi.cloudhealthtech.com/v1/aws_accounts',
            json=mock_schema_response
        )

        results = client.create(account_schema)

    assert results.id == 5909874999458


def test_delete(mock_schema_response):
    client = AwsAccountClient('fake_api_key')

    with requests_mock.Mocker() as m:
        m.get(
            'https://chapi.cloudhealthtech.com/v1/aws_accounts/5909874999458',
            json=mock_schema_response
        )
        m.delete(
            'https://chapi.cloudhealthtech.com/v1/aws_accounts/5909874999458'
        )

        results = client.delete('5909874999458')

    assert results.id is None


def test_get_spec_by_account_id(mock_schema_response):
    client = AwsAccountClient('fake_api_key')

    with requests_mock.Mocker() as m:
        m.get(
            'https://chapi.cloudhealthtech.com/v1/aws_accounts/5909874999458',
            json=mock_schema_response
        )
        results = client.get_by_account_id('5909874999458')

    assert results.name == 'bcttest1'


def test_get_spec_by_name():
    client = AwsAccountClient('fake_api_key')

    mock_list = {'aws_accounts': [
        {'id': 5909874999458, 'name': 'bcttest1',
         'amazon_name': 'bcttest1', 'owner_id': '619288149268',
         'hide_public_fields': False, 'region': 'global',
         'created_at': '2018-09-22T15:51:04Z',
         'updated_at': '2019-01-19T22:33:39Z', 'account_type': 'Standalone',
         'vpc_only': True, 'cluster_name': 'bcttest1',
         'status': {'level': 'yellow', 'last_update': '2019-01-20T17:43:30Z'},
         'authentication': {'protocol': 'assume_role',
                            'assume_role_arn': 'arn:aws:iam::619288149268:role/CloudHealth',
                            'assume_role_external_id': '27beaf0b252df5700240e09ea7e96d'},
         'billing': {'is_consolidated': False},
         'cloudtrail': {'enabled': False}, 'ecs': {'enabled': False},
         'aws_config': {'enabled': False}, 'cloudwatch': {'enabled': True},
         'tags': [], 'groups': [{'name': 'filter_test', 'group': 'Other'}],
         '_links': {'self': {'href': '/v1/aws_accounts/5909874999458'}}},
        {'id': 1511828494523, 'name': 'Joe Keegan',
         'amazon_name': 'Joe Keegan', 'owner_id': '899826514230',
         'hide_public_fields': False, 'region': 'global',
         'created_at': '2018-06-08T18:30:41Z',
         'updated_at': '2019-01-19T22:33:37Z', 'account_type': 'Standalone',
         'vpc_only': True, 'cluster_name': 'Joe Keegan',
         'status': {'level': 'yellow', 'last_update': '2019-01-20T17:43:29Z'},
         'authentication': {'protocol': 'assume_role',
                            'assume_role_arn': 'arn:aws:iam::899826514230:role/CloudHealth',
                            'assume_role_external_id': '27beaf0b252df5700240e09ea7e96d'},
         'billing': {'is_consolidated': False},
         'cloudtrail': {'enabled': False}, 'ecs': {'enabled': False},
         'aws_config': {'enabled': False}, 'cloudwatch': {'enabled': True},
         'tags': [], 'groups': [{'name': 'filter_test', 'group': 'Other'}],
         '_links': {'self': {'href': '/v1/aws_accounts/1511828494523'}}}
    ]}

    with requests_mock.Mocker() as m:
        m.get(
            'https://chapi.cloudhealthtech.com/v1/aws_accounts/',
              json=mock_list
        )
        results = client.get_by_name('bcttest1')

    assert results.owner_id == '619288149268'


def test_update(mock_schema_response):
    client = AwsAccountClient('fake_api_key')

    with requests_mock.Mocker() as m:
        m.put(
            'https://chapi.cloudhealthtech.com/v1/aws_accounts/5909874999458',
            json=mock_schema_response
        )
        m.get(
            'https://chapi.cloudhealthtech.com/v1/aws_accounts/5909874999458',
            json=mock_schema_response
        )

        results = client.update(mock_schema_response)

    assert results.id == 5909874999458

