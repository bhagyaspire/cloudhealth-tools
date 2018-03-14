#!/usr/bin/env python3
import argparse
import logging

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

    parser.add_argument('--ApiKey',
                        required=True,
                        help="CloudHealth API Key.")
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
                        required=True,
                        help="Path to the file containing the list of groups.")
    parser.add_argument('--CatchAllName',
                        help="If set, will create a catch-all group with this "
                             "name")
    parser.add_argument('--LogLevel',
                        default='warn',
                        help="Log level sent to the console.")
    return parser.parse_args()


def generate_schema(name, groups, tag=None, catchall_name=None):
    rules = []
    constants = []
    if tag:
        group_tag = tag
    else:
        group_tag = name
    for group_id, group_name in enumerate(groups):
        ref_id = group_id + 1
        rule = {
            "type": "filter",
            "asset": "AwsAsset",
            "to": ref_id,
            "condition": {
                "clauses": [{
                    "tag_field": [group_tag],
                    "op": "=",
                    "val": group_name
                }]
            }
        }
        constant = {
            "ref_id": ref_id,
            "name": group_name
        }
        rules.append(rule)
        constants.append(constant)

    if catchall_name:
        rule = {
            "type": "filter",
            "asset": "AwsAsset",
            "to": "999999999",
            "condition": {
                "clauses": [{
                    "tag_field": [group_tag],
                    "op": "Has A Value"
                }]
            }
        }

        constant = {
                "ref_id": "999999999",
                "name": catchall_name
            }
        rules.append(rule)
        constants.append(constant)

    schema = {
                "name": name,
                "include_in_reports": "true",
                "rules": rules,
                "merges": [],
                "constants": [
                    {"type": "Static Group",
                     "list": constants
                     }
                ]}

    return schema


def generate_constants(groups, tag=None, catchall_name=None):
    constants = []
    for group_id, group_name in enumerate(groups):
        ref_id = group_id + 1
        constant = {
            "ref_id": ref_id,
            "name": group_name
        }
        constants.append(constant)

    if catchall_name:
        constant = {
                "ref_id": "999999999",
                "name": catchall_name
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

    with open(args.GroupsFile) as groups_file:
        groups_list = [group.rstrip() for group in list(groups_file)]

    ch = CloudHealth(args.ApiKey, client_api_id=args.ClientApiId)
    perspective_client = ch.client('perspective')
    perspective = perspective_client.create(args.Name)

    if args.Tag:
        group_tag = args.Tag
    else:
        group_tag = args.Name

    constants_list = generate_constants(groups_list,
                                        args.Tag,
                                        args.CatchAllName)
    perspective.constants = constants_list
