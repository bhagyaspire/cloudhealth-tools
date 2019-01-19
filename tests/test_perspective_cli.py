import json
from unittest.mock import patch

import pytest

from chtools.perspective.cli import PerspectiveCliHandler
from chtools.perspective.data import Perspective


@patch('chtools.perspective.client.PerspectiveClient')
@patch('chtools.perspective.data.Perspective')
def test_create(mock_client, mock_perspective):
    mock_perspective.return_value.update_cloudhealth.return_value = True
    perspective = mock_perspective(None)
    perspective.name = 'tag_filter'
    perspective.id = '1234567890'

    mock_client.return_value.check_exists.return_value = False
    mock_client.return_value.create.return_value = perspective

    args = ['create', '--spec-file', 'tests/specs/tag_filter.yaml']
    handler = PerspectiveCliHandler(
        args,
        'fake_api_key',
        client=mock_client
    )
    handler.execute()
    assert handler._results == "Created Perspective tag_filter (https://apps.cloudhealthtech.com/perspectives/1234567890)"


def test_create_with_name():
    args = ['create', '--spec-file', 'tests/specs/tag_filter.yaml',
            '--name', 'perspective_name']
    with pytest.raises(RuntimeError):
        PerspectiveCliHandler(
            args,
            'fake_api_key'
        )


def test_create_with_spec_and_schema():
    args = ['create', '--spec-file', 'tests/specs/tag_filter.yaml',
            '--schema-file', 'tests/schemas/tag_filter.json']
    with pytest.raises(RuntimeError):
        PerspectiveCliHandler(
            args,
            'fake_api_key'
        )


@patch('chtools.perspective.client.PerspectiveClient')
def test_delete(mock_client):
    mock_client.return_value.delete.return_value = True

    args = ['delete', '--name', 'tag_filter']
    handler = PerspectiveCliHandler(
        args,
        'fake_api_key',
        client=mock_client
    )
    handler.execute()
    assert handler._results == "Deleted Perspective tag_filter"


@patch('chtools.perspective.client.PerspectiveClient')
def test_empty_archive(mock_client):
    mock_client.return_value.index.return_value = {
        '2954937502949': {'name': 'test1', 'active': False},
        '2954937502950': {'name': 'test2', 'active': False}
    }
    mock_client.return_value.delete.return_value = True

    args = ['empty-archive']
    handler = PerspectiveCliHandler(
        args,
        'fake_api_key',
        client=mock_client
    )
    handler.execute()
    assert handler._results == "Deleted Perspective test1\nDeleted Perspective test2"


@patch('chtools.perspective.client.PerspectiveClient')
def test_get_schema(mock_client):
    perspective = Perspective(None)
    perspective.schema = {
                'name': 'mocked',
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

    mock_client.return_value.get.return_value = perspective

    args = ['get-schema', '--name', 'tag_filter']
    handler = PerspectiveCliHandler(
        args,
        'fake_api_key',
        client=mock_client
    )
    handler.execute()
    assert handler._results == json.dumps(perspective.schema, indent=4)


@patch('chtools.perspective.client.PerspectiveClient')
def test_get_spec(mock_client):
    perspective = Perspective(None)
    perspective.schema = {
                'name': 'mocked',
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

    mock_client.return_value.get.return_value = perspective

    args = ['get-spec', '--name', 'tag_filter']
    handler = PerspectiveCliHandler(
        args,
        'fake_api_key',
        client=mock_client
    )
    handler.execute()
    assert handler._results == perspective.spec
