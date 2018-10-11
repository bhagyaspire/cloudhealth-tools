import argparse
import json
import logging
from operator import itemgetter
import os
import sys

import yaml

from chtools.lib.client import CloudHealth


def parse_args(arguments):
    parser = argparse.ArgumentParser(
        description="Create and manage perspectives from the command line. "
    )

    parser.add_argument('action',
                        choices=[
                            'create',
                            'delete',
                            'empty-archive',
                            'get-schema',
                            'get-spec',
                            'list',
                            'update'
                        ],
                        help='Perspective action to take.')
    parser.add_argument('--api-key',
                        help="CloudHealth API Key. May also be set via the "
                             "CH_API_KEY environmental variable.")
    parser.add_argument('--client-api-id',
                        help="CloudHealth client API ID.")
    parser.add_argument('--name',
                        help="Name of the perspective to get or delete. Name "
                             "for create or update will come from the spec "
                             "or schema file.")
    parser.add_argument('--spec-file',
                        help="Path to the file containing YAML spec used to "
                             "create or update the perspective.")
    parser.add_argument('--schema-file',
                        help="Path to the file containing JSON schema used to "
                             "create or update the perspective.")
    parser.add_argument('--log-level',
                        default='warn',
                        help="Log level sent to the console.")
    return parser.parse_args(args=arguments)


def read_schema_file(file_path):
    with open(file_path) as spec_file:
        spec = json.load(spec_file)
    return spec


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

    logger = logging.getLogger('chtools')
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

    if args.spec_file and args.schema_file:
        raise RuntimeError(
            "You can specify --spec-file or --schema-file but not both."
        )

    spec = None
    schema = None
    if args.action in ['create', 'update']:
        if args.name:
            raise RuntimeError(
                "Can not specify --name for create or update. "
                "Name will come from spec or schema file."
            )

        if args.spec_file:
            spec = read_spec_file(args.spec_file)
            perspective_name = spec['name']
        elif args.schema_file:
            schema = read_schema_file(args.schema_file)
            perspective_name = schema['name']
        else:
            raise RuntimeError(
                "--spec-file or --schema-file option must be set for "
                "create or update"
            )
    elif args.action in ['list', 'empty-archive']:
        # No --name needed for these actions
        pass
    else:
        if not args.name:
            raise RuntimeError(
                "Must specify --name for action {}".format(args.action)
            )
        else:
            perspective_name = args.name

    ch = CloudHealth(api_key, client_api_id=args.client_api_id)
    perspective_client = ch.client('perspective')

    if args.action == 'create':
        if perspective_client.check_exists(perspective_name):
            raise RuntimeError(
                "Perspective with name {} already exists, use 'update' if "
                "you'd like to update the perspective, otherwise use a "
                "different name. ".format(perspective_name)
            )

        perspective = perspective_client.create(perspective_name)
        if spec:
            perspective.spec = spec
        elif schema:
            perspective.schema = schema
        else:
            raise RuntimeError(
                "Neither spec or schema are defined."
            )
        perspective.update_cloudhealth()
        print("Created Perspective {} "
              "(https://apps.cloudhealthtech.com/perspectives/{})".format(
                perspective.name,
                perspective.id
              )
        )
    elif args.action == 'delete':
        perspective = perspective_client.get(perspective_name)
        perspective.delete()
    elif args.action == 'get-schema':
        perspective = perspective_client.get(perspective_name)
        print(json.dumps(perspective.schema, indent=4))
    elif args.action == 'get-spec':
        perspective = perspective_client.get(perspective_name)
        print(perspective.spec)
    elif args.action == 'empty-archive':
        index = perspective_client.index(active=False)
        for perspective_id in index.keys():
            perspective_client.delete(perspective_id)
    elif args.action == 'list':
        perspective_list = [('NAME', 'ID', 'ACTIVE'),
                            ('-----', '-----', '-----')]
        index = perspective_client.index()
        for perspective_id, perspective_info in index.items():
            perspective_list.append(
                (
                    perspective_info['name'][0:32],
                    perspective_id,
                    perspective_info['active']

                )
            )
        for line in perspective_list:
            print('{0:<33} {1:<15} {2}'.format(*line))
    elif args.action == 'update':
        perspective = perspective_client.get(perspective_name)
        if spec:
            perspective.spec = spec
        elif schema:
            perspective.schema = schema
        else:
            raise RuntimeError(
                "Neither spec or schema are defined."
            )
        perspective.update_cloudhealth()
        print(
            "Updated Perspective {} "
            "(https://apps.cloudhealthtech.com/perspectives/{})".format(
                perspective.name,
                perspective.id
            )
        )
    else:
        raise RuntimeError(
            "Unknown action: {}".format(args.action)
        )


if __name__ == "__main__":
    main()
