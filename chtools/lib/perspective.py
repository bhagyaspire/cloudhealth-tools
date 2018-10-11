import copy
import datetime
import logging
import yaml

from deepdiff import DeepDiff

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

    def create(self, perspective_name, schema=None, spec=None):
        """Creates perspective. By default schema will be 'empty'. """
        if not self.check_exists(perspective_name):
            perspective = Perspective(self._http_client)
            perspective.create(perspective_name,
                               schema=schema,
                               spec=spec)
        else:
            raise RuntimeError(
                "Perspective with name {} already exists.".format(
                    perspective_name
                )
            )
        return perspective

    def check_exists(self, name, active=None):
        """Checks if a perspective exists with the same name. Returns bool"""
        perspectives = self.index(active=active)
        for perspective_id, perspective_info in perspectives.items():
            if perspective_info['name'] == name:
                return True
        else:
            return False

    def delete(self, perspective_input):
        """Deletes perspective

        perspective_input can be name or id
        """
        perspective_id = self._get_perspective_id(perspective_input)
        perspective = Perspective(self._http_client,
                                  perspective_id=str(perspective_id))
        perspective.delete()

    def get(self, perspective_input):
        """Creates Perspective object with data from CloudHealth

        perspective_input can be name or id
        """
        perspective_id = self._get_perspective_id(perspective_input)
        perspective = Perspective(self._http_client,
                                  perspective_id=str(perspective_id))
        perspective.get_schema()
        # Ideally CH would return a 404 if a perspective didn't exist but
        # instead if returns with a perspective named "Empty" that is empty.
        if perspective.name == 'Empty':
            raise RuntimeError(
                "Perspective with name {} does not exist.".format(
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

    def update(self, perspective_input, schema=None, spec=None):
        """Updates perspective with specified id, using specified schema

        perspective_input can be name or id
        """
        perspective = self.get(perspective_input)
        perspective_name = perspective.name
        logger.warning(
            "Both schema and spec were provided, will just use schema"
        )
        if schema or spec:
            name = schema['name'] if schema.get('name') else spec['name']
            if perspective_name != name:
                raise RuntimeError(
                    "perspective_name {} does not match name {} in provided "
                    "schema or spec".format(perspective_name, name)
                )

        perspective.update_cloudhealth(schema)
        return perspective


class Perspective:
    # MVP requires the full schema for all operations
    # i.e. changing the perspectives name requires submitting a full schema
    # with just the name changed.
    def __init__(self, http_client, perspective_id=None):
        # Used to generate ref_id's for new groups.
        self._new_ref_id = 100
        self._http_client = http_client
        self._uri = 'v1/perspective_schemas'
        # Schema has includes several lists that can only include a single item
        # items that match these keys will be converted to/from a single
        # item list as needed
        self._single_item_list_keys = ['field', 'tag_field']

        if perspective_id:
            # This will set the perspective URL
            self.id = perspective_id
            self.get_schema()
        else:
            # This will skip setting the perspective URL,
            # as None isn't part of a valid URL
            self._id = None
            # Also sets the default "empty schema"
            self._schema = {
                'name': 'EMPTY',
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

    def __repr__(self):
        return str(self.schema)

    def _add_constant(self, constant_name, constant_type):
        # Return current ref_id if constant already exists
        ref_id = self._get_ref_id_by_name(constant_name)
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

        return ref_id

    def _add_rule(self, rule_definition):
        logger.debug("Adding Rule: {}".format(rule_definition))
        self._schema['rules'].append(rule_definition)

    def create(self, perspective_name, schema=None, spec=None):
        """Creates an empty perspective or one based on a provided schema"""
        logger.info("Creating perspective {}".format(perspective_name))
        if schema and spec:
            logger.debug(
                "Both schema and spec were provided, will just use schema"
            )

        if schema or spec:
            if schema and schema.get('name'):
                name = schema['name']
            else:
                name = spec['name']
            if perspective_name != name:
                raise RuntimeError(
                    "perspective_name {} does not match name {} in provided "
                    "schema or spec".format(perspective_name, name)
                )

        if schema:
            self._schema = schema
        elif spec:
            self.spec = spec
        else:
            # Just set name for existing empty schema
            self.name = perspective_name

        # If self.id is set that means we know the perspective already exists
        if not self.id:
            schema_data = {'schema': self._schema}
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
        # hard_delete can cause CloudHealth to return 500 errors if
        # perspective schema gets into a strange state delete_params = {
        # 'force': True, 'hard_delete': True}
        delete_params = {'force': True, 'hard_delete': True}
        response = self._http_client.delete(self._uri, params=delete_params)
        logger.debug(response)
        self._schema = None

    @property
    def _get_new_ref_id(self):
        """Generates new ref_ids that are not in the current schema"""
        while True:
            self._new_ref_id += 1
            # Check to make sure ref_id isn't already used in schema
            # If so go to next id
            constants = self.schema['constants']
            existing_ref_ids = []
            # These are the types of constant that have ref_ids we care about
            constant_types = ['Static Group', 'Dynamic Group Block']
            for constant in constants:
                if constant['type'] in constant_types:
                    ref_ids = [item['ref_id'] for item in constant['list']]
                    existing_ref_ids.extend(ref_ids)
            if str(self._new_ref_id) not in existing_ref_ids:
                break

        return str(self._new_ref_id)

    def _get_name_by_ref_id(self, ref_id):
        """Returns the name of a constant (i.e. group) with a specified ref_id
        """
        constant_types = ['Static Group', 'Dynamic Group Block']
        constants = [constant for constant in self.schema['constants']
                     if constant['type'] in constant_types]
        for constant in constants:
            for item in constant['list']:
                if item['ref_id'] == ref_id and not item.get('is_other'):
                    return item['name']
        # If we get here then no constant with the specified name has been
        # found.
        return None

    def _get_ref_id_by_name(self, constant_name):
        """Returns the ref_id of a constant (i.e. group) with a specified name

        None is returned if constant with ref_id doesn't exist. This is used
        to identify new groups that need to have a new ref_id generated for
        them.
        """
        constant_types = ['Static Group', 'Dynamic Group Block']
        constants = [constant for constant in self.schema['constants']
                     if constant['type'] in constant_types]
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
    def name(self):
        name = self.schema['name']
        return name

    @name.setter
    def name(self, new_name):
        self._schema['name'] = new_name

    @property
    def schema(self):
        if not self._schema:
            self.get_schema()

        return self._schema

    @schema.setter
    def schema(self, schema_input):
        self._schema = schema_input

    def _spec_from_schema(self):
        """Spec is never stored, but always generated on the fly based on
        current schema"""
        spec_dict = copy.deepcopy(self._schema)
        for rule in spec_dict['rules']:
            # categorize schema uses 'ref_id' instead of 'to'
            # we switch it to 'to' so it's consistent with the filter
            # rules and makes it easier to understand
            if rule.get('ref_id'):
                rule['to'] = rule['ref_id']
                del rule['ref_id']
            rule['to'] = self._get_name_by_ref_id(rule['to'])
            # categorize don't have conditions and or nested dicts
            for key, value in rule.items():
                if (key in self._single_item_list_keys
                        and type(value) is list):
                    if len(value) != 1:
                        raise RuntimeError(
                            "Expected {} in {} to have list "
                            "with just 1 item.".format(key, rule)
                        )
                    rule[key] = value[0]
            # filter rules have conditions that need to checked
            if rule.get('condition'):
                for clause in rule['condition']['clauses']:
                    for key, value in clause.items():
                        if (key in self._single_item_list_keys
                                and type(value) is list):
                            if len(value) != 1:
                                raise RuntimeError(
                                    "Expected {} in {} to have list "
                                    "with just 1 item.".format(key, clause)
                                )
                            clause[key] = value[0]

        # Combine rules that only differ by asset into a single rule
        # asset key will include a list of assets from each rule that was
        # combined
        #
        # This is a little tricky since we want to modify a list we also
        # want to iterate over.
        combined_rules = []
        rules = spec_dict['rules']
        # We make a copy of the list of rules
        for current_rule in list(rules):
            # For each rule from the copy we check to see if it is still in
            # the list of rules. If it is that means it hasn't been combined
            # yet and we will look to see if we can combine it with other rules
            # If we combine rules we removed them from the rules list.
            if current_rule in rules:
                # We remove the current rule we are evaluating,
                # so its not evaluated again
                rules.remove(current_rule)
                asset_types = [current_rule['asset']]
                # Make a copy of the remaining rules so we can iterate over it
                for rule in list(rules):
                    rule_diff = DeepDiff(current_rule, rule)
                    # If the only think that is different is "root['asset']"
                    # Then we can combine
                    values_changed = rule_diff.get('values_changed')
                    if (values_changed
                            and len(rule_diff.keys()) == 1
                            and len(values_changed.keys()) == 1
                            and values_changed.get("root['asset']")):
                        asset_types.append(rule['asset'])
                        rules.remove(rule)
                if len(asset_types) > 1:
                    current_rule['asset'] = asset_types
                combined_rules.append(current_rule)

        spec_dict['rules'] = combined_rules
        del spec_dict['merges']
        del spec_dict['constants']
        return spec_dict

    def _spec_rule_to_schema(self, rule):
        logger.debug(
            "Updating schema with spec rule: {}".format(rule)
        )
        # Support either 'to' or 'ref_id' as used by categorize rules
        constant_name = rule['to'] if rule['to'] else rule['ref_id']
        rule_type = rule['type'].lower()
        # Support using 'search' for type as it's called in the Web GUI
        if rule_type in ['filter', 'search']:
            rule['type'] = 'filter'
            constant_type = 'Static Group'
        elif rule_type == 'categorize':
            constant_type = 'Dynamic Group Block'
        else:
            raise RuntimeError(
                "Unknown rule_type: {}. "
                "Valid rule_types are: filter, search or categorize"
            )

        # _add_constant will return ref_id of either newly created group or
        # of existing group
        ref_id = self._add_constant(constant_name, constant_type)

        # Covert spec syntactical sugar to valid schema
        rule['to'] = ref_id
        if rule_type == 'categorize':
            rule['ref_id'] = rule['to']
            del rule['to']

        # Convert to single item lists where needed
        # categorize don't have conditions and or nested dicts
        for key, value in rule.items():
            if key in self._single_item_list_keys and type(value) is str:
                rule[key] = [value]
        # filter rules have conditions that need to checked
        if rule.get('condition'):
            for clause in rule['condition']['clauses']:
                for key, value in clause.items():
                    if (key in self._single_item_list_keys
                            and type(value) is str):
                        clause[key] = [value]
        self._add_rule(rule)

    @property
    def spec(self):
        spec_dict = self._spec_from_schema()
        spec_yaml = yaml.dump(spec_dict, default_flow_style=False)
        return spec_yaml

    @spec.setter
    def spec(self, spec_input):
        """Updates schema based on passed spec dict"""
        logger.debug(
            "Updated schema using spec: {}".format(spec_input)
        )
        self.name = spec_input['name']
        if spec_input.get('include_in_reports'):
            self.include_in_reports = spec_input['include_in_reports']
        # Remove all existing rules, they will be "over written" by the spec
        self.schema['rules'] = []
        for rule in spec_input['rules']:
            # Expand rule that contains multiple assets into multiple rules
            if type(rule['asset']) is list:
                logger.debug(
                    "rule asset includes a list {}. "
                    "Expanding into multiple rules.".format(rule['asset'])
                )
                for asset_type in rule['asset']:
                    new_rule = copy.deepcopy(rule)
                    new_rule['asset'] = asset_type
                    self._spec_rule_to_schema(new_rule)
            else:
                self._spec_rule_to_schema(rule)

    def update_cloudhealth(self, schema=None):
        """Updates cloud with objects state or with provided schema"""
        if schema:
            perspective_schema = schema
        else:
            perspective_schema = self.schema

        if self.id:
            # Dynamic Group constants are created and maintained by
            # CloudHealth. They should be stripped from the schema prior to
            # submitting them to the API.

            # create copy of schema dict with and then change copy
            schema_data = {'schema': dict(perspective_schema)}
            schema_data['schema']['constants'] = [
                constant for constant in schema_data['schema']['constants']
                if constant['type'] != 'Dynamic Group'
            ]

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
