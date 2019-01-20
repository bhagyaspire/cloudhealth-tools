#!/usr/bin/env python3
import argparse
import logging
import os
import sys

from chtools.aws_account.cli import AwsAccountCliHandler
from chtools.perspective.cli import PerspectiveCliHandler

logger = logging.getLogger('chtools')


def parse_args(arguments):
    parser = argparse.ArgumentParser(
        description="CLI to interact with CloudHealth.",
        add_help=False
    )

    parser.add_argument('service',
                        choices=[
                            'aws-account',
                            'perspective',
                            'help'
                        ],
                        help='CloudHealth service that you wish to '
                             'interact with.')
    parser.add_argument('--api-key',
                        help="CloudHealth API Key. May also be set via the "
                             "CH_API_KEY environmental variable.")
    parser.add_argument('--client-api-id',
                        help="CloudHealth client API ID.")
    parser.add_argument('--log-level',
                        default='info',
                        help="Log level sent to the console.")
    service_args, action_args = parser.parse_known_args(args=arguments)

    if service_args.service == 'help':
        parser.print_help()
        sys.exit(0)
    return service_args, action_args


def service_to_handler(service_name):
    name_to_handler = {
        'aws-account': AwsAccountCliHandler,
        'perspective': PerspectiveCliHandler
    }
    return name_to_handler[service_name]


def main(arguments=sys.argv[1:]):
    service_args, action_args = parse_args(arguments)

    logging_levels = {
        'debug':    logging.DEBUG,
        'info':     logging.INFO,
        'warn':     logging.WARN,
        'error':    logging.ERROR
    }
    log_level = logging_levels[service_args.log_level.lower()]

    logger.setLevel(log_level)
    console_handler = logging.StreamHandler()
    logger.addHandler(console_handler)

    if service_args.api_key:
        api_key = service_args.api_key
    elif os.environ.get('CH_API_KEY'):
        api_key = os.environ['CH_API_KEY']
    else:
        raise RuntimeError(
            "API KEY must be set with either --api-key or "
            "CH_API_KEY environment variable."
        )

    cli_handler_class = service_to_handler(service_args.service)
    cli_handler = cli_handler_class(
        action_args,
        api_key,
        client_api_id=service_args.client_api_id,
        log_level=log_level
    )
    cli_handler.execute()


def perspective_tool(arguments=sys.argv[1:]):
    """This exists to support the legacy 'perspective-tool'
    that is now part of chtools"""
    perspective_tool_logger = logging.getLogger('perspective_tool')
    perspective_tool_logger.setLevel(logging.WARN)
    console_handler = logging.StreamHandler()
    perspective_tool_logger.addHandler(console_handler)

    perspective_tool_logger.warning(
        "perspective-tool is depreciated, use 'chtools perspective' "
        "command instead."
    )
    arguments.insert(0, 'perspective')
    main(arguments=arguments)

if __name__ == "__main__":
    main()


