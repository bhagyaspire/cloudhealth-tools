#!/usr/bin/env python3
import argparse
import json
import logging
import os

from cloudhealth.client import CloudHealth


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create a simple perspective using a list of group names. "
                    "List is read from a file and a perspective is created "
                    "for each line in the file. By default the group name "
                    "will match a tag with the same value. A catch-all group "
                    "can also be created, which will match anything with the "
                    "tag, but does not belong to any other groups."
    )

    parser.add_argument('Action',
                        choices=['create-simple',
                                 'update-simple',
                                 'delete',
                                 'get-schema'],
                        help='Perspective action to take.')
    parser.add_argument('--ApiKey',
                        help="CloudHealth API Key. May also be set via the "
                             "CH_API_KEY environmental variable.")
    parser.add_argument('--ClientApiId',
                        help="CloudHealth client API ID.")
    parser.add_argument('--Name',
                        required=True,
                        help="Name of the perspective.")
    parser.add_argument('--Tag',
                        help="The name of the tag the perspective will use "
                             "for it's groups. Defaults to the same as the "
                             "perspective name.")
    parser.add_argument('--GroupsFile',
                        help="Path to the file containing the list of groups.")
    parser.add_argument('--CatchAllName',
                        help="If set, will create a catch all group with this "
                             "name")
    parser.add_argument('--LogLevel',
                        default='warn',
                        help="Log level sent to the console.")
    return parser.parse_args()


def generate_rules(groups, group_tag, catchall_group=None):
    rules = []
    for group_name, group_id in groups.items():
        asset_rule = {
            "type": "filter",
            "asset": "AwsAsset",
            "to": group_id,
            "condition": {
                "clauses": [{
                    "tag_field": [group_tag],
                    "op": "=",
                    "val": group_name
                }]
            }
        }

        emr_cluster_rule = {
            "type": "filter",
            "asset": "AwsEmrCluster",
            "to": group_id,
            "condition": {
                "clauses": [{
                    "tag_field": [group_tag],
                    "op": "=",
                    "val": group_name
                }]
            }
        }

        rules.append(asset_rule)
        rules.append(emr_cluster_rule)

    if catchall_group:
        rule = {
            "type": "filter",
            "asset": "AwsAsset",
            "to": catchall_group['ref_id'],
            "condition": {
                "clauses": [{
                    "tag_field": [group_tag],
                    "op": "Has A Value"
                }]
            }
        }

        rules.append(rule)

    return rules


def generate_constants(groups, catchall_group=None):
    constants = []
    for group_name, group_id in groups.items():
        constant = {
            "ref_id": group_id,
            "name": group_name
        }
        constants.append(constant)

    if catchall_group:
        constant = {
                "ref_id": catchall_group['ref_id'],
                "name": catchall_group['name']
            }
        constants.append(constant)

    return constants


if __name__ == "__main__":
    args = parse_args()
    logging_levels = {
        'debug':    logging.DEBUG,
        'info':     logging.INFO,
        'warn':     logging.WARN,
        'error':    logging.ERROR
    }
    log_level = logging_levels[args.LogLevel.lower()]

    logger = logging.getLogger('cloudhealth')
    logger.setLevel(log_level)
    console_handler = logging.StreamHandler()
    logger.addHandler(console_handler)

    if args.ApiKey:
        api_key = args.ApiKey
    elif os.environ.get('CH_API_KEY'):
        api_key = os.environ['CH_API_KEY']
    else:
        raise RuntimeError(
            "API KEY must be set with either --ApiKey or "
            "CH_API_KEY environment variable."
        )

    if args.Action in ['create-simple', 'update-simple']:
        if args.GroupsFile:
            with open(args.GroupsFile, encoding='utf-8-sig') as groups_file:
                groups_list = [group.rstrip() for group in list(groups_file)]
        else:
            raise RuntimeError(
                "GroupFile option must be set for create or update"
            )

    ch = CloudHealth(api_key, client_api_id=args.ClientApiId)
    perspective_client = ch.client('perspective')

    if args.Action == 'create-simple':
        if args.Tag:
            group_tag = args.Tag
        else:
            group_tag = args.Name

        group_dict = {}
        for number, group_name in enumerate(groups_list):
            # If duplicate then skip and log warning
            if group_dict.get(group_name) is not None:
                logger.warning(
                    "Skipping Duplicate Group Name {}".format(group_name)
                )
                continue
            group_id = number + 1
            group_dict[group_name] = str(group_id)

        perspective = perspective_client.create(args.Name)

        if args.CatchAllName:
            catchall_group = {'name': args.CatchAllName,
                              'ref_id': '999999999'}
        else:
            catchall_group = None
        constants_list = generate_constants(group_dict,
                                            catchall_group)
        perspective.constants = constants_list

        rules_list = generate_rules(group_dict,
                                    group_tag,
                                    catchall_group)
        perspective.rules = rules_list
        perspective.update_cloudhealth()
        print(perspective.id)
    elif args.Action == 'update-simple':
        perspective = perspective_client.get(args.Name)
        # Get the tag used by the first rule as the group_tag
        rules = perspective.rules
        group_tag = rules[0]['condition']['clauses'][0]['tag_field'][0]

        # first build a dict of existing groups and their IDs
        # Exclude the system create group with the 'is_other' flag
        existing_groups = {group['name']: group['ref_id']
                           for group in perspective.constants[0]['list']
                           if group.get('is_other') is None}

        group_dict = {}
        # if group exists then add it and it's id to group_dict,
        # otherwise add new group with a place holder id
        # (ch will generate a real id when group is created).
        for number, group_name in enumerate(groups_list):
            # If duplicate then skip and log warning
            if group_dict.get(group_name) is not None:
                logger.warning(
                    "Skipping Duplicate Group Name {}".format(group_name)
                )
                continue
            group_id = number + 1
            if group_name in existing_groups.keys():
                group_dict[group_name] = existing_groups[group_name]
            else:
                group_dict[group_name] = str(group_id)

        if args.CatchAllName:
            if existing_groups.get(args.CatchAllName):
                ref_id = existing_groups[args.CatchAllName]
            else:
                ref_id = '999999999'
            catchall_group = {'name': args.CatchAllName,
                              'ref_id': ref_id}
        else:
            catchall_group = None

        constants_list = generate_constants(group_dict,
                                            catchall_group)
        perspective.constants = constants_list

        rules_list = generate_rules(group_dict,
                                    group_tag,
                                    catchall_group)
        perspective.rules = rules_list
        perspective.update_cloudhealth()
        print(perspective.id)
    elif args.Action == 'delete':
        perspective = perspective_client.get(args.Name)
        perspective.delete()
    elif args.Action == 'get-schema':
        perspective = perspective_client.get(args.Name)
        print(json.dumps(perspective.schema))
