import logging

logger = logging.getLogger(__name__)


class AwsAccount:
    # Note account_id is the CloudHealth ID and not the AWS Account ID
    # AWS Account ID is referred to as Owner ID by CloudHealth
    def __init__(self, http_client, account_id=None, schema=None):
        # Used to generate ref_id's for new groups.
        self._http_client = http_client
        self._uri = 'v1/aws_accounts'

        if account_id:
            self._schema = {}
            # This will set the perspective URL
            self.id = account_id
            self.get_schema()
        elif schema:
            self.schema = schema
        else:
            # sets the default "empty schema"
            self._schema = {
                    'id': None,
                    'name': 'empty',
                    'hide_public_fields': False,
                    'region': 'global',
                    'authentication': {
                        'protocol': 'assume_role',
                        'assume_role_arn': None,
                        'assume_role_external_id': None
                    },
                    'billing': {},
                    'cloudtrail': {},
                    'ecs': {},
                    'aws_config': {},
                    'cloudwatch': {},
                    'tags': []
                }

    def delete(self):
        if not self._schema.get('id'):
            raise RuntimeError(
                "account id must be specified to be able to delete"
            )
        response = self._http_client.delete(self._uri)
        self._schema = {}

    def get_schema(self):
        """gets the latest schema from CloudHealth"""
        response = self._http_client.get(self._uri)
        self._schema = response

    @property
    def id(self):
        return self._schema.get('id')

    @id.setter
    def id(self, account_id):
        self._schema['id'] = account_id
        self._uri = self._uri + '/' + account_id

    @property
    def schema(self):
        if not self._schema:
            self.get_schema()

        return self._schema

    @schema.setter
    def schema(self, schema_input):
        self._schema = schema_input
        if self._schema.get('id'):
            self._uri = self._uri + '/' + str(self._schema['id'])
        if self._schema.get('_links'):
            del self._schema['_links']
