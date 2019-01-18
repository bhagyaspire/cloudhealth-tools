import logging
from abc import ABC, abstractmethod


class CliHandler(ABC):

    def __init__(self, args_list, api_key,
                 client_api_id=None,
                 client=None,
                 log_level=logging.INFO):
        self._args_list = args_list
        self._args = self._parse_args()
        self._api_key = api_key
        self._client_api_id = client_api_id
        self._client = client(api_key, client_api_id=None)
        self._log_level = log_level

    def execute(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(self._log_level)
        console_handler = logging.StreamHandler()
        logger.addHandler(console_handler)

        action_name = self._args.action.replace('-', '_')
        method_name = '_{}'.format(action_name)
        method = getattr(self, method_name)
        method()

    @abstractmethod
    def _parse_args(self):
        """Returns parsed args from self._args"""
        pass
