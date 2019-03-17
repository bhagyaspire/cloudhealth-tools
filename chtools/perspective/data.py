import copy
import datetime
import logging
import re

import yaml
from deepdiff import DeepDiff

logger = logging.getLogger(__name__)


class Perspective:
    def __init__(self, http_client, perspective_id=None):
        # Used to generate ref_id's for new groups.
        self._new_ref_id = 100
        self._http_client = http_client
        self._uri = 'v1/perspective_schemas'
        self._match_lowercase_tag_field = None
        self._match_lowercase_tag_val = None
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

            ref_id = self._get_new_ref_id()
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

    def _add_merge(self, merge_definition):
        logger.debug("Adding Merge: {}".format(merge_definition))
        self._schema['merges'].append(merge_definition)

    def _create_perspective(self):
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
            self._create_perspective()
        elif spec:
            # If perspective includes merges we will create the perspective
            # without the merges and then update it with the merges. This is
            # needed as the Dynamic Groups (and related ref_ids) needs to be
            # created by CloudHealth prior to the merges being applied.
            if spec.get('merges'):
                logger.debug(
                    "Spec includes merges, creating initial "
                    "perspective without merges."
                )
                spec_without_merges = copy.deepcopy(spec)
                del spec_without_merges['merges']
                self.spec = spec_without_merges
                self._create_perspective()
                logger.debug(
                    "Updating perspective with merges from Spec"
                )
                self.spec = spec
                self.update_cloudhealth()
            else:
                self.spec = spec
                self._create_perspective()
        else:
            # Just set name for existing empty schema
            self.name = perspective_name
            self._create_perspective()

    def delete(self):
        # Perspective Names are not reusable for a tenant even if they are
        # hard deleted. Rename perspective prior to delete to allow the name
        # to be reused
        timestamp = datetime.datetime.now()
        self.name = self.name + str(timestamp)
        logger.debug(
            "Renaming perspective to {}".format(self.name)
        )
        self.update_cloudhealth()
        # hard_delete can cause CloudHealth to return 500 errors if
        # perspective schema gets into a strange state delete_params = {
        # 'force': True, 'hard_delete': True}
        delete_params = {'force': True, 'hard_delete': True}
        response = self._http_client.delete(self._uri, params=delete_params)
        logger.debug(response)
        self._schema = None

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

    def _get_constant_by_name(self, constant_name, constant_type):
        """Returns the constant clause (i.e. group) for a specified name"""
        constant_types = ['Static Group',
                          'Dynamic Group Block',
                          'Dynamic Group']
        if constant_type not in constant_types:
            raise RuntimeError(
                "constant_type {} is not a valid.".format(constant_type)
            )

        constants = [constant for constant in self.schema['constants']
                     if constant['type'] == constant_type]
        for constant in constants:
            for item in constant['list']:
                if item['name'] == constant_name and not item.get('is_other'):
                    logger.debug(
                        "Found {} constant {} and returning: {}".format(
                            constant_type, constant_name, item
                        )
                    )
                    return item
        # If we get here then no constant with the specified name has been
        # found.
        logger.debug(
            "Unable to find {} constant {} and returning None".format(
                            constant_type, constant_name
                        )
        )
        return None

    def _get_constant_by_ref_id(self, ref_id):
        """Returns the constant clause (i.e. group) for a specified ref_id"""
        constant_types = ['Static Group',
                          'Dynamic Group Block',
                          'Dynamic Group']
        constants = [constant for constant in self.schema['constants']
                     if constant['type'] in constant_types]
        for constant in constants:
            for item in constant['list']:
                if item['ref_id'] == ref_id and not item.get('is_other'):
                    return item
        # If we get here then no constant with the specified ref_id has been
        # found.
        return None

    def _get_name_by_ref_id(self, ref_id):
        """Returns the name of a constant (i.e. group) with a specified ref_id
        """
        constant = self._get_constant_by_ref_id(ref_id)
        if constant:
            return constant['name']
        else:
            return None

    def _get_ref_id_by_name(self, constant_name, dynamic_group_block=None):
        """Returns the ref_id of a constant (i.e. group) with a specified name

        By default only Static Groups and Dynamic Group Blocks are searched.
        Dynamic Groups are searched if the name of the Dynamic Group Block
        is specified.

        None is returned if constant with ref_id doesn't exist. This is used
        to identify new groups that need to have a new ref_id generated for
        them.
        """
        if not dynamic_group_block:
            constants_list = []
            for constant in self.schema['constants']:
                if constant['type'] in ["Static Group", "Dynamic Group Block"]:
                    constants_list.extend(constant['list'])
        else:
            for constant in self.schema['constants']:
                if constant['type'] == "Dynamic Group Block":
                    dynamic_group_blocks = constant['list']
                elif constant['type'] == "Dynamic Group":
                    dynamic_groups = constant['list']

            blk_id = None
            for block in dynamic_group_blocks:
                if block['name'] == dynamic_group_block:
                    blk_id = block['ref_id']
                    break

            if not blk_id:
                raise RuntimeError(
                    "Unable to find Dynamic Group with name {}".format(
                        dynamic_group_block
                    )
                )

            constants_list = [
                constant for constant in dynamic_groups
                if constant['blk_id'] == blk_id
            ]

        for constant in constants_list:
                if (constant['name'] == constant_name
                        and not constant.get('is_other')):
                    return constant['ref_id']

        # If we get here then no constant with the specified name has been
        # found.
        return None

    def get_schema(self):
        """gets the latest schema from CloudHealth"""
        response = self._http_client.get(self._uri)
        schema = response['schema']

        # If the perspective has Dynamic Groups then sometimes crud and other
        #  invalid groups can be returned with the schema. An example of
        # this is a Dynamic Group that no longer exists. It seems
        # CloudHealth includes these when getting the schema, but will not
        # allow them to be submitted back when updating the schema. So we
        # need to filter them out.
        for constant in schema['constants']:
            if constant['type'] == 'Dynamic Group':
                dynamic_group_block = constant
                break
        else:
            dynamic_group_block = None

        if dynamic_group_block:
            valid_dynamic_groups = []
            for group in dynamic_group_block['list']:
                if group['blk_id'] != "":
                    valid_dynamic_groups.append(group)
                else:
                    logger.debug(
                        "Dynamic Group {} does not appear to be valid as in "
                        "being excluded form the Perspective object's "
                        "schema. ".format(group)
                    )

            dynamic_group_block['list'] = valid_dynamic_groups

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
    def match_lowercase_tag_field(self):
        return bool(self._match_lowercase_tag_field)

    @match_lowercase_tag_field.setter
    def match_lowercase_tag_field(self, value):
        """If this is set to true then perspective rules will be set to always
        match against the tag field name in all lower case as well.

        I.e. if the rule is matching for the value "Test" and this is set to
            True then a rule to match "test" will also be created.

        """
        self._match_lowercase_tag_field = bool(value)

    @property
    def match_lowercase_tag_val(self):
        return bool(self._match_lowercase_tag_val)

    @match_lowercase_tag_val.setter
    def match_lowercase_tag_val(self, value):
        """If this is set to true then perspective rules will be set to always
        match against the tag value in all lower case as well.

        I.e. if the rule is matching for the value "Test" and this is set to
            True then a rule to match "test" will also be created.

        """
        self._match_lowercase_tag_val = bool(value)

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

        merges = []
        for merge_clause in spec_dict['merges']:
            to_group = self._get_constant_by_ref_id(merge_clause['to'])
            from_groups = [
                self._get_name_by_ref_id(ref_id) for ref_id
                in merge_clause['from']
            ]

            merges.append(
                {
                    'name': self._get_name_by_ref_id(to_group['blk_id']),
                    'type': merge_clause['type'],
                    'to': to_group['name'],
                    'from': from_groups
                }
            )

        if merges:
            spec_dict['merges'] = merges
        else:
            del spec_dict['merges']

        del spec_dict['constants']
        return spec_dict

    def _spec_merge_to_schema(self, merge_spec):
        logger.debug(
            "Updating schema with spec merge: {}".format(merge_spec)
        )
        if (
                    (merge_spec.get('from')
                        and type(merge_spec['from']) is not list)
                or (merge_spec.get('from_regex')
                        and type(merge_spec['from_regex']) is not list)
        ):
            raise TypeError(
                "'from' in merge clause must be a list. "
                "Invalid merge clause: {}".format(merge_spec)
            )

        merge_type = merge_spec['type']
        dynamic_group = merge_spec['name']
        if merge_type == 'Group':
            to_ref_id = self._get_ref_id_by_name(
                merge_spec['to'],
                dynamic_group_block=dynamic_group
            )
            if to_ref_id is None:
                raise RuntimeError(
                    "Unable to get ref_id for group {} "
                    "used in merge: {}".format(merge_spec['to'], merge_spec)
                )

            if merge_spec.get('from_regex'):
                merge_spec['from'] = []
                for constant_clause in self.schema['constants']:
                    if constant_clause['type'] == 'Dynamic Group':
                        dynamic_groups = constant_clause['list']
                        break
                else:
                    raise RuntimeError(
                        "No Dynamic Group constant found."
                    )

                for from_regex in merge_spec['from_regex']:
                    pattern = re.compile(from_regex)
                    for group in dynamic_groups:
                        if (pattern.match(group['name'])
                                and group['name'] != merge_spec['to']):
                            logger.debug(
                                "Group {} ({}) matched regex pattern {}. "
                                "Will merge with {} ({})".format(
                                    group['name'],
                                    self._get_ref_id_by_name(
                                        group['name'],
                                        dynamic_group_block=dynamic_group
                                    ),
                                    from_regex,
                                    merge_spec['to'],
                                    self._get_ref_id_by_name(
                                        merge_spec['to'],
                                        dynamic_group_block=dynamic_group
                                    )
                                )
                            )
                            merge_spec['from'].append(group['name'])

            from_ref_ids = []
            for from_group in merge_spec['from']:
                from_ref_id = self._get_ref_id_by_name(
                    from_group,
                    dynamic_group_block=dynamic_group
                )
                if from_ref_id:
                    from_ref_ids.append(from_ref_id)
                else:
                    logger.warning(
                        "Unable to get ref_id for group '{}' "
                        "used in merge: {}. Perspectives sometimes get into "
                        "a strange state with groups that are no longer valid."
                        " Recreating the perspective is the only way resolve "
                        "this kind of issue as manging Dynamic Groups and "
                        "removing merges is not support by the CloudHealth "
                        "API. If the group doesn't appear to be a valid "
                        "group then this warning can be ignored.".format(
                            from_group, merge_spec)
                    )

            # And merge clause
            merge = {
                'type': 'Group',
                'to': to_ref_id,
                'from': from_ref_ids
            }
            self._add_merge(merge)
        else:
            raise RuntimeError(
                "Unknown merge type {} used in merge: {}".format(merge_type,
                                                                 merge_spec)
            )

    def _set_constant_fwd_to(self):
        """ Merges have two parts, one part that is specified in the merges
        clause. The other part is setting the 'fwd_to' key for each constant
        that is merged. This function goes through the merges clause and
        sets (or unsets) the 'fwd_to' as appropriate."""
        merge_mapping = {}
        for merge in self.schema['merges']:
            for from_ref_id in merge['from']:
                merge_mapping[from_ref_id] = merge['to']

        for constant_clause in self.schema['constants']:
            if constant_clause['type'] == 'Dynamic Group':
                dynamic_groups = constant_clause['list']
                break
        else:
            dynamic_groups = []

        for group in dynamic_groups:
            if merge_mapping.get(group['ref_id']):
                logger.debug(
                    'Setting group {} ({}) to forward to {} ({})'.format(
                        self._get_name_by_ref_id(group['ref_id']),
                        group['ref_id'],
                        self._get_name_by_ref_id(
                            merge_mapping[group['ref_id']]
                        ),
                        merge_mapping[group['ref_id']]
                    )
                )
                group['fwd_to'] = merge_mapping[group['ref_id']]
            # If not found in merge_mapping, but has 'fwd_to' this means
            # merge has been removed and needs to be removed from the group
            # config.
            elif group.get('fwd_to'):
                logger.debug(
                    "Unsetting fwd_to on group {} ({})".format(
                        self._get_name_by_ref_id(group['ref_id']),
                        group['ref_id']
                    )
                )
                del group['fwd_to']

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

        # Include matching on lower case tag values and/or
        # lower case tag field name if options are set
        if rule['type'] == 'filter':

            clauses = rule['condition']['clauses']

            if self.match_lowercase_tag_val:
                clauses = self._match_lowercase_clauses(
                    clauses,
                    'val'
                )

            if self.match_lowercase_tag_field:
                clauses = self._match_lowercase_clauses(
                    clauses,
                    'tag_field'
                )

            if self.match_lowercase_tag_val or self.match_lowercase_tag_field:
                if len(clauses) > 1:
                    combine_with = rule['condition'].get('combine_with')
                    if combine_with is None:
                        # If it's None then we add OR condition to support
                        # matching entered value OR lower case value
                        rule['condition']['combine_with'] = "OR"
                    elif combine_with != 'OR':
                        raise RuntimeError(
                            "lowercase matching only supports rules with "
                            "a combine_with of 'OR'. Rule does not have "
                            "supported combine_with: {}".format(rule)
                        )

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

    @staticmethod
    def _match_lowercase_clauses(clauses, field):
        """Takes a list of clauses and returns a new list to include matching
        of lower case values.

        clauses is the list of clauses and field is the field that lower case
        matching should be done against. I.e. tag_field or val.
        """
        new_clauses = []
        for clause in clauses:
            # Not all clauses will match on the field so only try and match
            # lower case if the rules has the field
            tag_value = clause.get(field)
            if tag_value and not tag_value.islower():
                new_clause = dict(clause)
                new_clause[field] = tag_value.lower()
                new_clauses.append(new_clause)
        clauses.extend(new_clauses)
        return clauses

    @property
    def spec(self):
        spec_dict = self._spec_from_schema()
        if self.match_lowercase_tag_field:
            spec_dict[
                'match_lowercase_tag_field'] = self.match_lowercase_tag_field
        if self.match_lowercase_tag_val:
            spec_dict['match_lowercase_tag_val'] = self.match_lowercase_tag_val
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
        if spec_input.get('match_lowercase_tag_field'):
            self.match_lowercase_tag_field = spec_input[
                'match_lowercase_tag_field'
            ]
        if spec_input.get('match_lowercase_tag_val'):
            self.match_lowercase_tag_val = spec_input[
                'match_lowercase_tag_val'
            ]
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

        # Remove all existing merges, they will be "over written" by the spec
        self.schema['merges'] = []
        for merge in spec_input.get('merges', []):
            # Dynamic Group Block must be created by CloudHealth before merges
            # can be defined.
            dynamic_block_name = merge['name']
            dynamic_block_constant = self._get_constant_by_name(
                dynamic_block_name,
                'Dynamic Group Block'
            )
            # ref_id generated by CloudHealth are 13 characters. If the
            # ref_id is less than that then we know it's something has been
            # added to the spec and has not been created in CloudHealth yet.
            if (not dynamic_block_constant
                    or len(dynamic_block_constant['ref_id']) < 13):
                raise RuntimeError(
                    "categorize rule for {} must be applied to the "
                    "perspective before merges can be defined. Resubmit this "
                    "spec once the spec without the merges has been "
                    "applied. ".format(dynamic_block_name)
                )
            self._spec_merge_to_schema(merge)
        self._set_constant_fwd_to()

    def update_cloudhealth(self):
        """Updates cloud with objects state or with provided schema"""
        if self.id:
            schema_data = {'schema': self.schema}

            response = self._http_client.put(self._uri,
                                             schema_data)
            self.get_schema()
        else:
            raise RuntimeError(
                "Perspective Id must be set to update_cloudhealth a "
                "perspective"
            )
