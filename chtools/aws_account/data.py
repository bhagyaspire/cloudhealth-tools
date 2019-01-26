import logging

logger = logging.getLogger(__name__)

NEW_ACCOUNT_SCHEMA = {
                    'name': None,
                    'hide_public_fields': False,
                    'region': 'global',
                    'authentication': {
                        'protocol': 'assume_role',
                        'assume_role_arn': None
                    },
                    'billing': {
                        "bucket": None
                    },
                    'cloudtrail': {},
                    'ecs': {},
                    'aws_config': {},
                    'cloudwatch': {},
                    'tags': []
                    }


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
            self._schema = NEW_ACCOUNT_SCHEMA

    @property
    def amazon_name(self):
        return self._schema.get('amazon_name')

    @amazon_name.setter
    def amazon_name(self, amazon_name):
        self._schema['amazon_name'] = amazon_name
        
    @property
    def assume_role_arn(self):
        return self._schema.get('assume_role_arn')

    @assume_role_arn.setter
    def assume_role_arn(self, assume_role_arn):
        self._schema['assume_role_arn'] = assume_role_arn

    @property
    def assume_role_external_id(self):
        return self._schema['authentication'].get('assume_role_external_id')

    def create(self):
        if self.id:
            raise RuntimeError(
                'AwsAccount id must not be set. Use update_cloudhealth to '
                'update an existing AwsAccount'
            )

        if not self.name:
            raise RuntimeError(
                'AwsAccount name must be set before it can be created in '
                'CloudHealht'
            )

        self._schema['authentication'][
            'assume_role_external_id'] = self._generate_external_id()
        response = self._http_client.post(self._uri, self.schema)
        self.schema = response
        return response

    @property
    def dbr_bucket(self):
        return self._schema['billing'].get('bucket')

    @dbr_bucket.setter
    def dbr_bucket(self, bucket_name):
        self._schema['billing']['bucket'] = bucket_name

    def delete(self):
        if not self._schema.get('id'):
            raise RuntimeError(
                "account id must be specified to be able to delete"
            )
        self._http_client.delete(self._uri)
        self._schema = {}

    def get_schema(self):
        """gets the latest schema from CloudHealth"""
        response = self._http_client.get(self._uri)
        self._schema = response

    def _generate_external_id(self):
        response = self._http_client.get(
            'v1/aws_accounts/:id/generate_external_id'
        )
        return response['generated_external_id']

    @property
    def id(self):
        return self._schema.get('id')

    @id.setter
    def id(self, account_id):
        if self._schema.get('id'):
            raise ValueError(
                "Unable to change an AwsAccount Object's id. "
                "Create a new object with the desired id."
            )
        else:
            self._schema['id'] = account_id
            self._uri = self._uri + '/' + account_id

    @property
    def name(self):
        return self._schema.get('name')

    @name.setter
    def name(self, name):
        self._schema['name'] = name
        
    @property
    def owner_id(self):
        return self._schema.get('owner_id')

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

    def update_cloudhealth(self):
        if self.id:
            response = self._http_client.put(self._uri,
                                             self._schema)
            self.get_schema()
        else:
            raise RuntimeError(
                'AwsAccount id must be set to update CloudHealth'
            )
