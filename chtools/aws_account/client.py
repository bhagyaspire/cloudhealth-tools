import logging

from chtools.cloudhealth.client import CloudHealthClient
from chtools.aws_account.data import AwsAccount

logger = logging.getLogger(__name__)


class AwsAccountClient(CloudHealthClient):
    def __init__(self, api_key, client_api_id=None):
        super().__init__(api_key, client_api_id=client_api_id)
        self._uri = 'v1/aws_accounts/'

    def create(self, schema):
        aws_account = AwsAccount(self._http_client,
                                 schema=schema)
        aws_account.create()
        return aws_account

    def delete(self, account_id):
        aws_account = AwsAccount(self._http_client,
                                 account_id=account_id)
        aws_account.delete()
        return aws_account

    def get_by_account_id(self, account_id):
        aws_account = AwsAccount(self._http_client,
                                 account_id=account_id)
        return aws_account

    def get_by_owner_id(self, owner_id):
        aws_accounts = self.list()
        aws_account = None
        for schema in aws_accounts:
            if schema.get('owner_id') == owner_id:
                aws_account = AwsAccount(self._http_client,
                                         schema=schema)
                break
        return aws_account

    def get_by_name(self, name):
        aws_accounts = self.list()
        aws_account = None
        for schema in aws_accounts:
            if schema.get('name') == name:
                aws_account = AwsAccount(self._http_client,
                                         schema=schema)
                break
        return aws_account

    def list(self):
        # While the CloudHealth API has pagination, it does not provide any
        # indication that pagination is needed. We ask for a set page size,
        # and if the page is less than that sizer we know that pagination
        # is not needed.
        page_size = 100
        aws_accounts = []

        # CH API starts page numbers 1
        page = 1
        while True:
            response = self._http_client.get(
                self._uri,
                params={
                    'per_page': str(page_size),
                    'page': str(page)
                }
            )
            aws_accounts.extend(response['aws_accounts'])
            account_count = len(response['aws_accounts'])
            if account_count == page_size:
                page += 1
                logger.debug(
                    "Page was max size, retrieving next "
                    "page {}".format(str(page))
                )
            else:
                break

        return aws_accounts

    def update(self, schema):
        aws_account = AwsAccount(self._http_client,
                                 schema=schema)
        aws_account.update_cloudhealth()
        return aws_account
