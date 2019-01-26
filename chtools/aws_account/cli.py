#!/usr/bin/env python3
import argparse
import json
import logging
import sys

import yaml

from chtools.cli.handler import CliHandler
from chtools.cli.file import read_spec_file, read_schema_file
from chtools.aws_account.client import AwsAccountClient
from chtools.aws_account.data import NEW_ACCOUNT_SCHEMA


class AwsAccountCliHandler(CliHandler):

    def __init__(self, args_list, api_key,
                 client_api_id=None,
                 client=AwsAccountClient,
                 log_level=logging.INFO):
        super().__init__(
            args_list,
            api_key,
            client_api_id=client_api_id,
            client=client,
            log_level=log_level
        )

    def _create(self):
        if self._args.schema_file:
            schema = read_schema_file(self._args.schema_file)
        elif self._args.spec_file:
            schema = read_spec_file(self._args.spec_file)
        else:
            schema = dict(NEW_ACCOUNT_SCHEMA)
            schema['name'] = self._args.name
            if self._args.assume_role_arn:
                schema['authentication'][
                    'assume_role_arn'] = self._args.assume_role_arn
            if self._args.dbr_bucket:
                schema['billing']['bucket'] = self._args.dbr_bucket

        aws_account = self._client.create(schema)
        results = (
            "Created AWS Account {} "
            "(https://apps.cloudhealthtech.com/aws_accounts/{}/edit)".format(
                aws_account.name,
                aws_account.id
            )
        )
        return results

    def _delete(self):
        aws_account = self._get_aws_account()
        account_name = aws_account.name
        aws_account.delete()
        results = (
            "Deleted AWS Account {}".format(account_name)
        )
        return results

    def _get_aws_account(self):
        if self._args.account_id:
            aws_account = self._client.get_by_account_id(self._args.account_id)
            account_info = "Account Id {}".format(self._args.account_id)
        elif self._args.owner_id:
            aws_account = self._client.get_by_owner_id(self._args.owner_id)
            account_info = "Owner Id {}".format(self._args.owner_id)
        elif self._args.name:
            aws_account = self._client.get_by_name(self._args.name)
            account_info = "Name {}".format(self._args.name)
        else:
            raise ValueError(
                "Arguments needed to get-schema not set."
            )

        if aws_account.schema:
            results = aws_account
        else:
            raise RuntimeError(
                "unable to retrieve schema for AWS Account {}".format(
                    account_info
                )
            )
        return results

    def _get_schema(self):
        aws_account = self._get_aws_account()
        results = json.dumps(aws_account.schema, indent=4)
        return results

    def _get_spec(self):
        aws_account = json.loads(self._get_schema())
        results = yaml.dump(aws_account.schema, default_flow_style=False)
        return results

    def _parse_args(self):
        parser = argparse.ArgumentParser(
            description="Create and manage AWS Accounts",
            prog="chtools aws-account",
            add_help=False
        )

        parser.add_argument('action',
                            choices=[
                                'create',
                                'delete',
                                'get-schema',
                                'get-spec',
                                'help',
                                'list',
                                'update'
                            ],
                            help='Account action to take.')

        parser.add_argument('--account-id',
                            help="CloudHealth Account Id for the AWS Account "
                                 "to interact with. "
                                 "Can not specify with --name "
                                 "or --owner-id."
                            )
        parser.add_argument('--assume-role-arn',
                            help="The ARN of the role that account should "
                                 "use to connect to the AWS Account"
                            )
        parser.add_argument('--dbr-bucket',
                            help="The name of the bucket used to store "
                                 "the DBR reports."
                            )
        parser.add_argument('--name',
                            help="Name of the AWS Account to interact with. "
                                 "Can not specify with --account-id "
                                 "or --owner-id when getting schema or spec. "
                                 "Specifying name with create or update with "
                                 "change the accounts name."
                            )
        parser.add_argument('--owner-id',
                            help="AWS Account Id for the AWS Account "
                                 "to interact with. "
                                 "Can not specify with --name "
                                 "or --account-id."
                            )
        parser.add_argument('--spec-file',
                            help="Path to the YAML spec file to create "
                                 "or update an AWS Account."
                            )
        parser.add_argument('--schema-file',
                            help="Path to the JSON spec file to create "
                                 "or update an AWS Account."
                            )

        args = parser.parse_args(args=self._args_list)
        if args.action == 'help':
            parser.print_help()
            sys.exit(0)

        if args.action in ['get-schema', 'get-spec']:
            if args.assume_role_arn:
                raise ValueError(
                    '--assume-role-arn not accepted for {}'.format(args.action)
                )
            if args.dbr_bucket:
                raise ValueError(
                    '--dbr-bucket not accepted for {}'.format(args.action)
                )
            if args.spec_file:
                raise ValueError(
                    '--spec-file not accepted for {}'.format(args.action)
                )
            if args.schema_file:
                raise ValueError(
                    '--schema-file not accepted for {}'.format(args.action)
                )
        if args.action in ['get-schema', 'get-spec', 'update']:
            if not args.account_id and not args.owner_id and not args.name:
                raise ValueError(
                    "Must specify --account-id, --owner-id or --name"
                )
            if sum([bool(args.account_id),
                    bool(args.owner_id),
                    bool(args.name)]) > 1:
                raise ValueError(
                    "Only --account-id, --owner-id or --name can be "
                    "specified. You can not specify more than one."
                )
        if args.action in ['create', 'update']:
            if args.spec_file and args.schema_file:
                raise ValueError(
                    "May only specify --spec-file or --schema-file not both."
                )
            if ((args.name or args.assume_role_arn or args.dbr_bucket)
                    and (args.spec_file or args.schema_file)):
                raise ValueError(
                    "Can not specify --name, --assume-role-arn or "
                    "--dbr-bucket along with --spec-file or --schema-file"
                )
        if args.action in ['create']:
            if args.account_id:
                raise ValueError(
                    '--account-id not accepted for {}'.format(args.action)
                )
            if args.owner_id:
                raise ValueError(
                    '--owner-id not accepted for {}'.format(args.action)
                )
        if args.action in ['update']:
            if (not args.name and not args.assume_role_arn
                    and not args.dbr_bucket and not args.spec_file
                    and not args.schema_file):
                raise ValueError(
                    "Must specify --spec-file or --schema-file or at least "
                    "one of the following: --name, --assume-role-arn or "
                    "--dbr-bucket along"
                )

        return args

    def _list(self):
        account_list = [
            ('Account Name', 'Amazon Name', 'Owner Id', 'Account Type', 'Status'),
            ('------------', '-----------', '--------', '------------', '------')
        ]
        accounts = self._client.list()
        for account in sorted(accounts, key=lambda a: a['name'].lower()):
            account_list.append(
                (
                    account.get('name', '')[0:24],
                    account.get('amazon_name', '')[0:24],
                    account.get('owner_id', '')[0:12],
                    account.get('account_type')[0:12],
                    account['status'].get('level')
                )
            )

        formatted_lines = []
        for line in account_list:
            formatted_lines.append(
                '{0:<24} {1:<24} {2:<12} {3:<12} {4}'.format(*line)
            )

        results = "\n".join(formatted_lines)
        return results

    def _update(self):
        if self._args.schema_file:
            schema = read_schema_file(self._args.schema_file)
        elif self._args.spec_file:
            schema = read_spec_file(self._args.spec_file)
        else:
            aws_account = self._get_aws_account()
            if self._args.assume_role_arn:
                aws_account.assume_role_arn = self._args.assume_role_arn
            if self._args.dbr_bucket:
                aws_account.dbr_bucket = self._args.dbr_bucket
            if self._args.name:
                aws_account.name = self._args.name
            schema = aws_account.schema

        aws_account = self._client.update(schema)
        results = (
            "Updated AWS Account {} "
            "(https://apps.cloudhealthtech.com/aws_accounts/{}/edit)".format(
                aws_account.name,
                aws_account.id
            )
        )
        return results

