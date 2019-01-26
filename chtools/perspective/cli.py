#!/usr/bin/env python3
import argparse
import json
import logging
import sys

import yaml

from chtools.cli.handler import CliHandler
from chtools.perspective.client import PerspectiveClient
from chtools.cli.file import read_schema_file, read_spec_file

logger = logging.getLogger(__name__)


class PerspectiveCliHandler(CliHandler):

    def __init__(self, args_list, api_key,
                 client_api_id=None,
                 client=PerspectiveClient,
                 log_level=logging.INFO):
        super().__init__(
            args_list,
            api_key,
            client_api_id=client_api_id,
            client=client,
            log_level=log_level
        )

    def _create(self):
        if self._client.check_exists(self._args.name):
            raise RuntimeError(
                "Perspective with name {} already exists, use 'update' if "
                "you'd like to update the perspective, otherwise use a "
                "different name. ".format(self._args.name)
            )

        if self._args.spec_file:
            spec = read_spec_file(self._args.spec_file)
            perspective = self._client.create(spec['name'], spec=spec)
        elif self._args.schema_file:
            schema = read_schema_file(self._args.schema_file)
            perspective = self._client.create(schema['name'], schema=schema)
        else:
            raise RuntimeError(
                "Neither spec or schema are defined."
            )

        # perspective.update_cloudhealth()
        results = (
            "Created Perspective {} "
            "(https://apps.cloudhealthtech.com/perspectives/{})".format(
                perspective.name,
                perspective.id
              )
        )
        return results

    def _delete(self):
        self._client.delete(self._args.name)
        results = (
            "Deleted Perspective {}".format(self._args.name)
        )
        return results

    def _empty_archive(self):
        index = self._client.index(active=False)
        deleted_perspectives = []
        for perspective_id, perspective_info in index.items():
            self._client.delete(perspective_id)
            deleted_perspectives.append(
                "Deleted Perspective {}".format(perspective_info['name'])
            )
        return "\n".join(deleted_perspectives)

    def _get_schema(self):
        perspective = self._client.get(self._args.name)
        results = json.dumps(perspective.schema, indent=4)
        return results

    def _get_spec(self):
        perspective = self._client.get(self._args.name)
        results = perspective.spec
        return results

    def _parse_args(self):
        parser = argparse.ArgumentParser(
            description="Create and manage perspectives",
            prog="chtools perspective",
            add_help=False
        )

        parser.add_argument('action',
                            choices=[
                                'create',
                                'delete',
                                'empty-archive',
                                'get-schema',
                                'get-spec',
                                'help',
                                'list',
                                'update'
                            ],
                            help='Perspective action to take.')
        parser.add_argument('--name',
                            help="Name of the perspective to get or delete. "
                                 "Name for create or update will come from the"
                                 " spec or schema file.")
        parser.add_argument('--spec-file',
                            help="Path to the file containing YAML spec used "
                                 "to create or update the perspective.")
        parser.add_argument('--schema-file',
                            help="Path to the file containing JSON schema "
                                 "used to create or update the perspective.")

        args = parser.parse_args(args=self._args_list)
        if args.action == 'help':
            parser.print_help()
            sys.exit(0)

        if args.action in ['create', 'update']:
            if args.name:
                raise RuntimeError(
                    "Can not specify --name for create or update. "
                    "Name will come from spec or schema file."
                )
            if not args.spec_file and not args.schema_file:
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

        if args.spec_file and args.schema_file:
            raise RuntimeError(
                "You can specify --spec-file or --schema-file but not both."
            )

        return args

    def _list(self):
        perspective_list = [('NAME', 'ID', 'ACTIVE'),
                            ('-----', '-----', '-----')]
        index = self._client.index()
        for perspective_id, perspective_info in index.items():
            perspective_list.append(
                (
                    perspective_info['name'][0:32],
                    perspective_id,
                    perspective_info['active']

                )
            )

        formatted_lines = []
        for line in perspective_list:
            formatted_lines.append('{0:<33} {1:<15} {2}'.format(*line))

        results = "\n".join(formatted_lines)
        return results

    @staticmethod
    def _read_schema_file(file_path):
        with open(file_path) as schema_file:
            schema = json.load(schema_file)
        return schema

    @staticmethod
    def _read_spec_file(file_path):
        with open(file_path) as spec_file:
            spec = yaml.load(spec_file)
        return spec

    def _update(self):
        if self._args.spec_file:
            spec = read_spec_file(self._args.spec_file)
            perspective = self._client.update(spec['name'], spec=spec)
        else:
            schema = read_schema_file(self._args.schema_file)
            perspective = self._client.update(schema['name'], schema=schema)

        results = (
            "Updated Perspective {} "
            "(https://apps.cloudhealthtech.com/perspectives/{})".format(
                perspective.name,
                perspective.id
            )
        )
        return results
