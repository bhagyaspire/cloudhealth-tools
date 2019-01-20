import pytest
import requests_mock

from chtools.aws_account.client import AwsAccountClient


# def test_get_spec_by_account_id():
#     client = AwsAccountClient('94bf81b5-ea3f-4fa5-b93b-4d908f7dc9c1',
#                               client_api_id='5366')
#
#     results = client.get_by_account_id('5909874999458')
#     assert results.name == 'bctlinktest1'