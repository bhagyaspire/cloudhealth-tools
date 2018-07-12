import argparse
import json
import logging
import os
import sys

import yaml

from chtools.lib.client import CloudHealth


def parse_args(arguments):
    parser = argparse.ArgumentParser(
        description="Create and manage perspectives via YAML spec files. "
                    "Tool can also be used to delete perspective or print a "
                    "perspective's JSON schema. "
    )

    parser.add_argument('action',
                        choices=['create',
                                 'update',
                                 'delete',
                                 'get-schema'],
                        help='Perspective action to take.')
    parser.add_argument('--api-key',
                        help="CloudHealth API Key. May also be set via the "
                             "CH_API_KEY environmental variable.")
    parser.add_argument('--client-api-id',
                        help="CloudHealth client API ID.")
    parser.add_argument('--name',
                        help="Name of the perspective to get or delete. Name "
                             "for create or update will come from the spec "
                             "file")
    parser.add_argument('--spec-file',
                        help="Path to the file containing spec for the "
                             "perspective.")
    parser.add_argument('--log-level',
                        default='warn',
                        help="Log level sent to the console.")
    return parser.parse_args(args=arguments)


def read_spec_file(file_path):
    with open(file_path) as spec_file:
        spec = yaml.load(spec_file)
    return spec


def main(arguments=sys.argv[1:]):
    args = parse_args(arguments)
    logging_levels = {
        'debug':    logging.DEBUG,
        'info':     logging.INFO,
        'warn':     logging.WARN,
        'error':    logging.ERROR
    }
    log_level = logging_levels[args.log_level.lower()]

    logger = logging.getLogger('cloudhealth')
    logger.setLevel(log_level)
    console_handler = logging.StreamHandler()
    logger.addHandler(console_handler)

    if args.api_key:
        api_key = args.api_key
    elif os.environ.get('CH_API_KEY'):
        api_key = os.environ['CH_API_KEY']
    else:
        raise RuntimeError(
            "API KEY must be set with either --api-key or "
            "CH_API_KEY environment variable."
        )

    if args.action in ['create', 'update']:
        if args.spec_file:
            spec = read_spec_file(args.spec_file)
        else:
            raise RuntimeError(
                "--spec-file option must be set for create or update"
            )

    ch = CloudHealth(api_key, client_api_id=args.client_api_id)
    perspective_client = ch.client('perspective')

    if args.action == 'create':
        perspective_name = spec['Name']

        if perspective_client.check_exists(perspective_name):
            raise RuntimeError(
                "Perspective with name {} already exists, use 'update' if "
                "you'd like to update the perspective, otherwise use a "
                "different name. ".format(perspective_name)
            )

        perspective = perspective_client.create(perspective_name)
        perspective.update_spec(spec)
        perspective.update_cloudhealth()
        print("Created Perspective {} "
              "(https://apps.cloudhealthtech.com/perspectives/{})".format(
                perspective.name,
                perspective.id
              )
        )
    elif args.action == 'update':
        perspective_name = spec['Name']
        perspective = perspective_client.get(perspective_name)
        perspective.update_spec(spec)
        perspective.update_cloudhealth()
        print("Updated Perspective {} "
              "(https://apps.cloudhealthtech.com/perspectives/{})".format(
                perspective.name,
                perspective.id
              )
        )
    elif args.action == 'delete':
        perspective = perspective_client.get(args.name)
        perspective.delete()
    elif args.action == 'get-schema':
        perspective = perspective_client.get(args.name)
        print(json.dumps(perspective.schema, indent=4))


if __name__ == "__main__":
    main()
