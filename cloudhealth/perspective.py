class Perspectives:
    def __init__(self, http_client):
        self._http_client = http_client
        self._uri = 'v1/perspective_schemas/'

    def list(self):
        """Returns dict of PerspectiveIds, Names and Active Status"""
        response = self._http_client.get(self._uri)
        return response

    def get(self, perspective_id):
        """Creates Perspective object with data from CloudHealth"""
        perspective = Perspective(self._http_client, perspective_id)
        perspective.get_config()
        # Ideally CH would return a 404 if a perspective didn't exist but
        # instead if returns with a perspective named "Empty" that is empty.
        if perspective.name == 'Empty':
            raise RuntimeError(
                "Perspective with id {} does not exist.".format(perspective_id)
            )
        return perspective


class Perspective:

    def __init__(self, http_client, perspective_id):
        self._http_client = http_client
        self._uri = 'v1/perspective_schemas/' + perspective_id

        self._config = None

    def get_config(self):
        response = self._http_client.get(self._uri)
        self._config = response['schema']

    @property
    def config(self):
        if not self._config:
            self.get_config()

        return self._config

    @property
    def name(self):
        name = self.config['name']
        return name

    @property
    def rules(self):
        rules = self.config['rules']
        return rules

    @property
    def constants(self):
        constants = self.config['constants']
        return constants

    @property
    def merges(self):
        constants = self.config['merges']
        return merges
