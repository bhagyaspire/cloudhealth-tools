import datetime
from operator import itemgetter
import logging

logger = logging.getLogger(__name__)


class PerspectiveClient:
    def __init__(self, http_client):
        self._http_client = http_client
        self._uri = 'v1/perspective_schemas/'

    def _get_perspective_id(self, perspective_input):
        """Returns the perspective id based on input.

        Determines if perspective is an id (i.e. int) or a name. If name will
        make API call to determine it's id
        """
        try:
            int(perspective_input)
            return str(perspective_input)
        except ValueError:
            perspectives = self.index()
            for perspective_id, perspective_info in perspectives.items():
                if perspective_info['name'] == perspective_input:
                    return perspective_id

    def create(self, name):
        """Creates perspective. Schema will be 'empty'. """
        perspective = Perspective(self._http_client)
        perspective.create(name)
        return perspective

    def delete(self, perspective_input):
        perspective_id = self._get_perspective_id(perspective_input)
        perspective = Perspective(self._http_client,
                                  perspective_id=str(perspective_id))
        perspective.delete()

    def get(self, perspective_input):
        """Creates Perspective object with data from CloudHealth"""
        perspective_id = self._get_perspective_id(perspective_input)
        perspective = Perspective(self._http_client,
                                  perspective_id=str(perspective_id))
        perspective.get_schema()
        # Ideally CH would return a 404 if a perspective didn't exist but
        # instead if returns with a perspective named "Empty" that is empty.
        if perspective.name == 'Empty':
            raise RuntimeError(
                "Perspective with id {} does not exist.".format(perspective)
            )
        return perspective

    def index(self, active=None):
        """Returns dict of PerspectiveIds, Names and Active Status"""
        response = self._http_client.get(self._uri)
        if active is None:
            perspectives = response
        else:
            perspectives = {
                perspective_id: perspective_info for
                perspective_id, perspective_info in response.items()
                if perspective_info['active'] == active
            }
        return perspectives

    def update(self, perspective_input, schema):
        """Updates perspective with specified id, using specified schema"""
        perspective = self.get(perspective_input)
        perspective.update_cloudhealth(schema)
        return perspective


class Perspective:
    # MVP requires the full schema for all operations
    # i.e. changing the perspectives name requires submitting a full schema
    # with just the name changed.
    def __init__(self, http_client, perspective_id=None, schema=None):
        self._http_client = http_client
        self._uri = 'v1/perspective_schemas'

        if perspective_id:
            # This will set the perspective URL
            self.id = perspective_id
        else:
            # This will skip setting the perspective URL,
            # as None isn't part of a valid URL
            self._id = None

        if schema:
            self._schema = schema
        else:
            self._schema = None

    def __repr__(self):
        return str(self.schema)

    @property
    def constants(self):
        constants = self.schema['constants']
        return constants

    @constants.setter
    def constants(self, constants_list):
        # Sort list alphabetically
        # While we sort here, looks like the rules need to be sorted too
        # Sorting rules is more complicated, so dropping from scope
        constants_list = sorted(constants_list, key=itemgetter('name'))

        # See if is_other rules is included, if not add it
        if not any('is_other' in constants
                   for constants in constants_list):
            other_rule = {
                        'name': 'Other',
                        'ref_id': '1234567890',
                        'is_other': 'true'
                    }
            constants_list.append(other_rule)
        constants_schema = [{'type': 'Static Group', 'list': constants_list}]
        self._schema['constants'] = constants_schema

    def create(self, name, schema=None):
        """Creates an empty perspective or one based on a provided schema"""
        if schema is None:
            schema = {
                'name': name,
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

        if not self.id:
            schema_data = {'schema': schema}
            response = self._http_client.post(self._uri, schema_data)
            perspective_id = response['message'].split(" ")[1]
            self.id = perspective_id
            self.get_schema()
        else:
            raise RuntimeError(
                "Perspective with Id {} exists. Use update_cloudhealth instead".format(
                    self.id
                )
            )

    def delete(self):
        # Perspective Names are not reusable for a tenant even if they are
        # hard deleted. Rename perspective prior to delete to allow the name
        # to be reused
        timestamp = datetime.datetime.now()
        self.name = self.name + str(timestamp)
        self.update_cloudhealth()
        delete_params = {'force': True, 'hard_delete': True}
        response = self._http_client.delete(self._uri, params=delete_params)
        self.schema = None

    def get_schema(self):
        """gets the latest schema from CloudHealth"""
        response = self._http_client.get(self._uri)
        self._schema = response['schema']

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, perspective_id):
        self._id = perspective_id
        self._uri = self._uri + '/' + perspective_id

    @property
    def merges(self):
        merges = self.schema['merges']
        return merges

    @property
    def name(self):
        name = self.schema['name']
        return name

    @name.setter
    def name(self, new_name):
        self.schema['name'] = new_name

    @property
    def rules(self):
        rules = self.schema['rules']
        return rules

    @rules.setter
    def rules(self, rules_list):
        self._schema['rules'] = rules_list

    @property
    def schema(self):
        if not self._schema:
            self.get_schema()

        return self._schema

    @schema.setter
    def schema(self, schema):
        self._schema = schema

    def update_cloudhealth(self, schema=None):
        """Updates cloud with objects state or with provided schema"""
        if schema:
            perspective_schema = schema
        else:
            perspective_schema = self.schema

        if self.id:
            schema_data = {'schema': perspective_schema}
            response = self._http_client.put(self._uri, schema_data)
            self.get_schema()
        else:
            raise RuntimeError(
                "Perspective Id must be set to update_cloudhealth a "
                "perspective".format(self.id)
            )





