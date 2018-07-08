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
                "Perspective with id {} does not exist.".format(
                    perspective_input
                )
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
        # Used to generate ref_id's for new groups.
        self._new_ref_id = 100
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

    def _add_constant(self, constant_name, constant_type):
        # Return current ref_id if constant already exists
        ref_id = self._get_ref_id_by_name(constant_name,
                                          constant_type=constant_type)
        if ref_id:
            logger.debug(
                "constant {} {} already exists with ref_id {}".format(
                    constant_name,
                    constant_type,
                    ref_id
                )
            )
        # If constant doesn't exist, i.e. ref_id is none, then create constant
        else:
            # Look through existing constants for the type we are adding.
            # There will always be a 'Static Group' constant.
            for item in self.schema['constants']:
                if item['type'] == constant_type:
                    constant = item
                    break
                # Create a constant for the type if it doesn't already exist.
                else:
                    constant = {
                                "type": constant_type,
                                "list": []
                    }
                    self.schema['constants'].append(constant)

            ref_id = self._get_new_ref_id
            logger.debug(
                "creating constant {} {} with ref_id {}".format(
                    constant_name,
                    constant_type,
                    ref_id
                )
            )
            new_group = {
                'ref_id': ref_id,
                'name': constant_name
            }
            constant['list'].append(new_group)

            # If Dynamic then the placeholder group for the Dynamic Group
            # is needed. CloudHealth will put in real values once the schema
            # is submitted.
            if constant_type == 'Dynamic Group Block':
                dynamic_group = {
                                    "type": "Dynamic Group",
                                    "list": [{
                                        "ref_id": "123456",
                                        "blk_id": ref_id,
                                        "val": "placeholder",
                                        "name": "placeholder"
                                    }]
                                }
                self.schema['constants'].append(dynamic_group)

        return ref_id

    def _add_rule(self, rule_type, asset_type, ref_id, tag_name, tag_values):
        clauses = []

        if rule_type == 'filter':
            if type(tag_values) is list:
                for tag_value in tag_values:
                    clause = {
                        "tag_field": [tag_name],
                        "op": "=",
                        "val": tag_value
                    }
                    clauses.append(clause)
            elif type(tag_values) is bool:
                if tag_values:
                    clause = {
                        "tag_field": [tag_name],
                        "op": "Has A Value"
                    }
                    clauses.append(clause)
                else:
                    clause = {
                        "tag_field": [tag_name],
                        "op": "Is Missing Field"
                    }
                    clauses.append(clause)

            condition = {
                "clauses": clauses
            }
            if len(clauses) > 1:
                condition['combine_with'] = 'OR'

            rule = {
                "type": "filter",
                "asset": asset_type,
                "to": ref_id,
                "condition": condition
            }
        elif rule_type == 'categorize':
            rule = {
                        "type": "categorize",
                        "asset": asset_type,
                        "tag_field": [tag_name],
                        "ref_id": ref_id,
                        "name": tag_name
                    }

        self._schema['rules'].append(rule)

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
                "Perspective with Id {} exists. Use update_cloudhealth "
                "instead".format(self.id)
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
        self._schema = None

    @staticmethod
    def _expand_group_by_tag_value(group):
        conditions = group['Conditions']
        if len(conditions) != 1:
            raise RuntimeError(
                "GroupByTagValue only supports a single condition. The "
                "following conditions were specified: {}".format(conditions)
            )
        assets = group['Assets']
        tag_name = conditions[0]['Name']
        tag_values = conditions[0]['Values']
        expanded_groups = []

        for tag_value in tag_values:
            expanded_group = {
                'Name': tag_value,
                'Type': 'Search',
                'Assets': assets,
                'Conditions': [
                    {
                        'Type': 'Tag',
                        'Name': tag_name,
                        'Values': [tag_value]
                    }
                ]
            }
            expanded_groups.append(expanded_group)
        return expanded_groups

    @property
    def _get_new_ref_id(self):
        self._new_ref_id += 1
        return self._new_ref_id

    def _get_ref_id_by_name(self, constant_name, constant_type="Static Group"):
        constants = [constant for constant in self.constants
                     if constant['type'] == constant_type]
        for constant in constants:
            for item in constant['list']:
                if item['name'] == constant_name and not item.get('is_other'):
                    return item['ref_id']
        # If we get here then no constant with the specified name has been
        # found.
        return None

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
    def include_in_reports(self):
        include_in_reports = self.schema['include_in_reports']
        return include_in_reports

    @include_in_reports.setter
    def include_in_reports(self, toggle):
        self._schema['include_in_reports'] = toggle

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
        self._schema['name'] = new_name

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

    def _spec_group_to_schema(self, group):
        group_name = group['Name']
        group_type = group['Type']
        assets = group['Assets']
        conditions = group['Conditions']
        if group_type == 'Search':
            rule_type = 'filter'
            constant_type = 'Static Group'
        elif group_type == 'Categorize':
            rule_type = 'categorize'
            constant_type = 'Dynamic Group Block'
        else:
            raise RuntimeError(
                "Unknown group type {}".format(group_type)
            )

        # _add_constant will return ref_id of either newly created group or
        # of existing group
        ref_id = self._add_constant(group_name, constant_type)

        for asset in assets:
            for condition in conditions:
                if condition['Type'] == 'Tag':
                    tag_name = condition['Name']
                    # Categorize rules don't have tag values
                    tag_values = condition.get('Values')

                    self._add_rule(rule_type,
                                   asset,
                                   ref_id,
                                   tag_name,
                                   tag_values)
                else:
                    raise RuntimeError(
                        "Unknown condition type {} in group: {}".format(
                            condition['Type'],
                            group
                        )
                    )

    def update_schema(self, schema):
        self._schema = schema

    def update_spec(self, spec):
        logger.debug(
            "Updated schema using spec: {}".format(spec)
        )
        self.name = spec['Name']
        if spec.get('Reports'):
            self.include_in_reports = spec['Reports']

        for group in spec['Groups']:
            # If GroupByTagValue then expand groups and add each expanded
            # group to the schema.
            if group['Type'] == 'GroupByTagValue':
                expanded_groups = self._expand_group_by_tag_value(group)
                for expanded_group in expanded_groups:
                    self._spec_group_to_schema(expanded_group)
            else:
                # If not GroupByTagValue then just add the group to the schema
                self._spec_group_to_schema(group)

    def update_cloudhealth(self, schema=None):
        """Updates cloud with objects state or with provided schema"""
        if schema:
            perspective_schema = schema
        else:
            perspective_schema = self.schema

        if self.id:
            schema_data = {'schema': perspective_schema}
            update_params = {'allow_group_delete': True}
            response = self._http_client.put(self._uri,
                                             schema_data,
                                             params=update_params)
            self.get_schema()
        else:
            raise RuntimeError(
                "Perspective Id must be set to update_cloudhealth a "
                "perspective".format(self.id)
            )
