import logging

from chtools.cloudhealth.client import CloudHealthClient
from chtools.perspective.data import Perspective

logger = logging.getLogger(__name__)


class PerspectiveClient(CloudHealthClient):
    def __init__(self, api_key, client_api_id=None):
        super().__init__(api_key, client_api_id=client_api_id)
        self._uri = 'v1/perspective_schemas/'

    def _get_perspective_id(self, perspective_input):
        """Returns the perspective id based on input.

        Determines if perspective is an id (i.e. int) or a name. If name will
        make API call to determine it's id
        """
        try:
            int(perspective_input)
            return str(perspective_input)
        except ValueError:
            perspectives = self.index()
            for perspective_id, perspective_info in perspectives.items():
                if perspective_info['name'] == perspective_input:
                    return perspective_id

    def create(self, perspective_name, schema=None, spec=None):
        """Creates perspective. By default schema will be 'empty'. """
        if not self.check_exists(perspective_name):
            perspective = Perspective(self._http_client)
            perspective.create(perspective_name,
                               schema=schema,
                               spec=spec)
        else:
            raise RuntimeError(
                "Perspective with name {} already exists.".format(
                    perspective_name
                )
            )
        return perspective

    def check_exists(self, name, active=None):
        """Checks if a perspective exists with the same name. Returns bool"""
        perspectives = self.index(active=active)
        for perspective_id, perspective_info in perspectives.items():
            if perspective_info['name'] == name:
                return True
        else:
            return False

    def delete(self, perspective_input):
        """Deletes perspective

        perspective_input can be name or id
        """
        perspective_id = self._get_perspective_id(perspective_input)
        perspective = Perspective(self._http_client,
                                  perspective_id=str(perspective_id))
        perspective.delete()
        # returned perspective will have schema set to None
        return perspective

    def get(self, perspective_input):
        """Creates Perspective object with data from CloudHealth

        perspective_input can be name or id
        """
        perspective_id = self._get_perspective_id(perspective_input)
        perspective = Perspective(self._http_client,
                                  perspective_id=str(perspective_id))
        perspective.get_schema()
        # Ideally CH would return a 404 if a perspective didn't exist but
        # instead if returns with a perspective named "Empty" that is empty.
        if perspective.name == 'Empty':
            raise RuntimeError(
                "Perspective with name {} does not exist.".format(
                    perspective_input
                )
            )
        return perspective

    def index(self, active=None):
        """Returns dict of PerspectiveIds, Names and Active Status"""
        response = self._http_client.get(self._uri)
        if active is None:
            perspectives = response
        else:
            perspectives = {
                perspective_id: perspective_info for
                perspective_id, perspective_info in response.items()
                if perspective_info['active'] == active
            }
        return perspectives

    def update(self, perspective_input, schema=None, spec=None):
        """Updates perspective with specified id, using specified schema

        perspective_input can be name or id
        """
        if not schema and not spec:
            raise ValueError(
                "Must provide either schema or spec"
            )

        if schema and spec:
            raise ValueError(
                "must provide schema or spec, not both"
            )

        perspective = self.get(perspective_input)

        if schema:
            if schema['name'] != perspective.name:
                raise ValueError(
                    "perspective_name {} does not match name {} in provided "
                    "schema or spec".format(schema['name'], perspective.name)
                )
            perspective.schema = schema
        else:
            if spec['name'] != perspective.name:
                raise ValueError(
                    "perspective_name {} does not match name {} in provided "
                    "schema or spec".format(spec['name'], perspective.name)
                )
            perspective.spec = spec

        perspective.update_cloudhealth()
        return perspective


