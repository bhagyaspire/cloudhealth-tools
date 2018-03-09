class Perspectives:
    def __init__(self, http_client):
        self._http_client = http_client
        self._uri = 'v1/perspective_schemas/'

    def index(self):
        """Returns dict of PerspectiveIds, Names and Active Status"""
        response = self._http_client.get(self._uri)
        return response

    def get(self, perspective_id):
        """Creates Perspective object with data from CloudHealth"""
        perspective = Perspective(self._http_client,
                                  perspective_id=perspective_id)
        perspective.get_schema()
        # Ideally CH would return a 404 if a perspective didn't exist but
        # instead if returns with a perspective named "Empty" that is empty.
        if perspective.name == 'Empty':
            raise RuntimeError(
                "Perspective with id {} does not exist.".format(perspective_id)
            )
        return perspective

    def create(self, schema):
        """Creates perspective based on provided schema dict"""
        perspective = Perspective(self._http_client, schema=schema)
        perspective.create()
        return perspective


class Perspective:
    # MVP requires the full schema for all operations
    # i.e. changing the perspectives name requires submitting a full schema
    # with just the name changed.
    def __init__(self, http_client, perspective_id=None, schema=None):
        self._http_client = http_client
        self._uri = 'v1/perspective_schemas'

        if perspective_id:
            self._uri = self._uri + '/' + perspective_id
            self._id = perspective_id
        else:
            self._id = None

        if schema:
            self._schema = schema
        else:
            self._schema = None

    def __repr__(self):
        return str(self.schema)

    @property
    def constants(self):
        constants = self.schema['constants']
        return constants

    def create(self):
        """Posts Schema to CloudHealth to create new perspective"""
        if not self.id:
            schema_data = {'schema': self.schema}
            response = self._http_client.post(self._uri, schema_data)
            perspective_id = response['message'].split(" ")[1]
            self._id = perspective_id
        else:
            raise RuntimeError(
                "Perspective with Id {} exists. Use update instead".format(
                    self.id
                )
            )

    def get_schema(self):
        """get's latest schema from CloudHealth"""
        response = self._http_client.get(self._uri)
        self._schema = response['schema']

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, perspective_id):
        self._id = perspective_id

    @property
    def merges(self):
        merges = self.schema['merges']
        return merges

    @property
    def name(self):
        name = self.schema['name']
        return name

    @property
    def rules(self):
        rules = self.schema['rules']
        return rules

    @property
    def schema(self):
        if not self._schema:
            self.get_schema()

        return self._schema

    @schema.setter
    def schema(self, schema):
        self._schema = schema






