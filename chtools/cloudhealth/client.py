import json
import logging

import requests

logger = logging.getLogger(__name__)

DEFAULT_CLOUDHEALTH_API_URL = 'https://chapi.cloudhealthtech.com/'


class HTTPClient:
    def __init__(self, endpoint, api_key, client_api_id=None):
        self._endpoint = endpoint
        self._headers = {'Content-type': 'application/json'}
        self._params = {'api_key': api_key,
                        'client_api_id': client_api_id}

    def _http_call(self, method, uri, data=None, additional_params=None):
        url = self._endpoint + uri
        # Would be ideal to have better handling in the future, but just
        # need to support dicts for now
        if data is None:
            post_data = None
        elif type(data) is dict:
            post_data = json.dumps(data)
        elif type(data) is str:
            post_data = data
        else:
            raise TypeError(
                "data must either be dict or string (i.e. JSON)"
            )

        http_call = getattr(requests, method)
        call_params = self._params
        if additional_params:
            call_params.update(additional_params)
        logger.debug("{} {} with params: {}".format(method.upper(),
                                                    url,
                                                    call_params))
        if data:
            logger.debug("{} Data: {}".format(method.upper(), post_data))
        response = http_call(url,
                             params=call_params,
                             headers=self._headers,
                             data=post_data)

        # Sometimes in error conditions valid json is not returned
        try:
            response_message = response.json()
        except json.decoder.JSONDecodeError:
            response_message = response.text

        if response.status_code < 200 or response.status_code > 299:
            raise RuntimeError(
                ('Request to {} failed! HTTP Error Code: {} '
                 'Response: {}').format(
                    url, response.status_code, response_message))

        if response_message:
            logger.debug(
                "Response: {}".format(response_message)
            )
            return response_message

    def delete(self, uri, params=None):
        return self._http_call('delete', uri, additional_params=params)

    def get(self, uri, params=None):
        return self._http_call('get', uri, additional_params=params)

    def post(self, uri, data, params=None):
        return self._http_call('post', uri, data=data, additional_params=params)

    def put(self, uri, data, params=None):
        return self._http_call('put', uri, data=data, additional_params=params)

    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, param_dict):
        self._params = param_dict

    def add_param(self, param):
        params = self.params
        params.update(param)
        self.params = params


class CloudHealthClient:

    def __init__(self, api_key, client_api_id=None, http_client=HTTPClient):
        self._api_key = api_key
        self._client_api_id = client_api_id
        self._http_client = http_client(
                     DEFAULT_CLOUDHEALTH_API_URL,
                     api_key=api_key,
                     client_api_id=client_api_id
        )

