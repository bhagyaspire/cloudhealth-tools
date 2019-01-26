import json
from unittest.mock import patch

import pytest

from chtools.aws_account.cli import AwsAccountCliHandler
from chtools.aws_account.data import AwsAccount


@pytest.fixture()
def mock_schema():
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


@patch('chtools.aws_account.client.AwsAccountClient')
def test_create_account_from_spec(mock_client, mock_schema):
    aws_account = AwsAccount(None, schema=mock_schema)
    mock_client.return_value.create.return_value = aws_account

    args = ['create', '--spec-file', 'tests/account_data/test_spec.yaml']
    handler = AwsAccountCliHandler(
        args,
        'fake_api_key',
        client=mock_client
    )
    handler.execute()
    assert 'Created AWS Account bcttest1' in handler._results


@patch('chtools.aws_account.client.AwsAccountClient')
def test_create_account_from_arg(mock_client, mock_schema):
    aws_account = AwsAccount(None, schema=mock_schema)
    mock_client.return_value.create.return_value = aws_account

    args = ['create', '--name', 'bcttest1']
    handler = AwsAccountCliHandler(
        args,
        'fake_api_key',
        client=mock_client
    )
    handler.execute()
    assert 'Created AWS Account bcttest1' in handler._results


@patch('chtools.aws_account.client.AwsAccountClient')
def test_get_schema_by_name(mock_client, mock_schema):
    aws_account = AwsAccount(None, schema=mock_schema)
    mock_client.return_value.get_by_name.return_value = aws_account

    args = ['get-schema', '--name', 'bcttest1']
    handler = AwsAccountCliHandler(
        args,
        'fake_api_key',
        client=mock_client
    )
    handler.execute()
    assert handler._results == json.dumps(aws_account.schema, indent=4)


@patch('chtools.aws_account.client.AwsAccountClient')
def test_update_account_by_owner_id_from_arg(mock_client, mock_schema):
    aws_account = AwsAccount(None, schema=mock_schema)
    mock_client.return_value.update.return_value = aws_account

    args = ['update', '--name', 'bcttest1',
            '--assume-role-arn', 'arn:aws:iam::619288149268:role/CloudHealth']
    handler = AwsAccountCliHandler(
        args,
        'fake_api_key',
        client=mock_client
    )
    handler.execute()
    assert 'Updated AWS Account bcttest1' in handler._results



