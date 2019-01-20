#!/usr/bin/env python3
import argparse
import json
import logging
import sys


from chtools.cli.handler import CliHandler
from chtools.aws_account.client import AwsAccountClient


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

    def _delete(self):
        if self._args.owner_id:
            aws_account = self._client.get_by_owner_id(self._args.owner_id)
            account_info = "Owner Id {}".format(self._args.owner_id)
        elif self._args.name:
            aws_account = self._client.get_by_name(self._args.name)
            account_info = "Name {}".format(self._args.name)
        else:
            aws_account = self._client.get_by_account_id(self._args.account_id)
            account_info = "Account Id {}".format(self._args.account_id)

        aws_account.delete()
        results = (
            "Deleted AWS Account {}".format(account_info)
        )
        return results

    def _get_schema(self):

        if self._args.account_id:
            aws_account = self._client.get_by_account_id(self._args.account_id)
        elif self._args.owner_id:
            aws_account = self._client.get_by_owner_id(self._args.owner_id)
        elif self._args.name:
            aws_account = self._client.get_by_name(self._args.name)
        else:
            raise ValueError(
                "Arguments needed to get-schema not set."
            )

        results = json.dumps(aws_account.schema, indent=4)
        return results

    def _parse_args(self):
        parser = argparse.ArgumentParser(
            description="Create and manage AWS Accounts",
            add_help=False
        )

        parser.add_argument('action',
                            choices=[
                                'delete',
                                'get-schema',
                                'help',
                                'list'
                            ],
                            help='Account action to take.')
        parser.add_argument('--name',
                            help="Name of the AWS Account to interact with. "
                                 "Name for create or update will come from the"
                                 " spec or schema file. "
                                 "Can not specify with --account-id "
                                 "or --owner-id"
                            )
        parser.add_argument('--account-id',
                            help="CloudHealth Account Id for the AWS Account "
                                 "to interact with. "
                                 "Can not specify with --name "
                                 "or --owner-id"
                            )
        parser.add_argument('--owner-id',
                            help="AWS Account Id for the AWS Account "
                                 "to interact with. "
                                 "Can not specify with --name "
                                 "or --account-id"
                            )

        args = parser.parse_args(args=self._args_list)
        if args.action == 'help':
            parser.print_help()
            sys.exit(0)

        if sum([bool(args.account_id),
                bool(args.owner_id),
                bool(args.name)]) > 1:
            raise ValueError(
                "Only --account-id, --owner-id or --name can be specified. "
                "You can not specify more than one."
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
                    account.get('name', ''),
                    account.get('amazon_name', ''),
                    account.get('owner_id', ''),
                    account.get('account_type'),
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

