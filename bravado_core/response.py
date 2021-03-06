from six import iteritems

from bravado_core.content_type import APP_JSON
from bravado_core.unmarshal import unmarshal_schema_object
from bravado_core.validate import validate_schema_object
from bravado_core.exception import MatchingResponseNotFound, SwaggerMappingError

# Response bodies considered to be empty
EMPTY_BODIES = (None, '', '{}', 'null')


class IncomingResponse(object):
    """
    Interface for incoming client-side response objects.

    Subclasses are responsible for providing attrs for __required_attrs__.
    """
    __required_attrs__ = [
        'reason',       # string - http reason phrase
        'status_code',  # int - http status code
        'text',         # string - raw text of the body
    ]

    def __getattr__(self, name):
        """
        When an attempt to access a required attribute that doesn't exist
        is made, let the caller know that the type is non-compliant in its
        attempt to be `IncomingResponse`. This is in place of the usual throwing
        of an AttributeError.

        Reminder: __getattr___ is only called when it has already been
                  determined that this object does not have the given attr.

        :raises: NotImplementedError when the subclass has not provided access
                to a required attribute.
        """
        if name in self.__required_attrs__:
            raise NotImplementedError(
                'This IncomingResponse type {0} forgot to implement an attr '
                'for `{1}`'.format(type(self), name))
        raise AttributeError(
            "'{0}' object has no attribute '{1}'".format(type(self), name))

    def json(self, **kwargs):
        """
        :return: response content in a json-like form
        :rtype: int, float, double, string, unicode, list, dict
        """
        raise NotImplementedError("Implement json() in {0}".format(type(self)))

    def __str__(self):
        return '{0} {1}'.format(self.status_code, self.reason)


class OutgoingResponse(object):
    """
    Interface for outgoing server-side response objects.
    """
    # TODO: charset needed?
    __required_attrs__ = [
        'content_type',  # str
        'text',          # str of body
        'headers',       # dict of headers
    ]

    def __getattr__(self, name):
        """
        :raises: NotImplementedError when the subclass has not provided access
                to a required attribute.
        """
        if name in self.__required_attrs__:
            raise NotImplementedError(
                'This OutgoingResponse type {0} forgot to implement an attr'
                ' for `{1}`'.format(type(self), name))
        raise AttributeError(
            "'{0}' object has no attribute '{1}'".format(type(self), name))

    def json(self, **kwargs):
        """
        :return: response content in a json-like form
        :rtype: int, float, double, string, unicode, list, dict
        """
        raise NotImplementedError("Implement json() in {0}".format(type(self)))


def unmarshal_response(response, op):
    """Unmarshal incoming http response into a value based on the
    response specification.

    :type response: :class:`bravado_core.response.IncomingResponse`
    :type op: :class:`bravado_core.operation.Operation`
    :returns: value where type(value) matches response_spec['schema']['type']
        if it exists, None otherwise.
    """
    response_spec = get_response_spec(response.status_code, op)

    def has_content(response_spec):
        return 'schema' in response_spec

    if not has_content(response_spec):
        return None

    # TODO: Non-json response contents
    content_spec = response_spec['schema']
    content_value = response.json()

    if op.swagger_spec.config['validate_responses']:
        validate_schema_object(op.swagger_spec, content_spec, content_value)

    return unmarshal_schema_object(
        op.swagger_spec, content_spec, content_value)


def get_response_spec(status_code, op):
    """Given the http status_code of an operation invocation's response, figure
    out which response specification it maps to.

    #/paths/
        {path_name}/
            {http_method}/
                responses/
                    {status_code}/
                        {response}

    :type status_code: int
    :type op: :class:`bravado_core.operation.Operation`
    :return: response specification
    :rtype: dict
    :raises: MatchingResponseNotFound when the status_code could not be mapped
        to a response specification.
    """
    # We don't need to worry about checking #/responses/ because jsonref has
    # already inlined the $refs
    response_specs = op.op_spec.get('responses')
    default_response_spec = response_specs.get('default', None)
    response_spec = response_specs.get(str(status_code), default_response_spec)
    if response_spec is None:
        raise MatchingResponseNotFound(
            "Response specification matching http status_code {0} not found "
            "for operation {1}. Either add a response specification for the "
            "status_code or use a `default` response.".format(status_code, op))
    return response_spec


def validate_response(response_spec, op, response):
    """
    Validate an outgoing response against its Swagger specification.

    :type response_spec: dict
    :type op: :class:`bravado_core.operation.Operation`
    :type response: :class:`bravado_core.response.OutgoingResponse`
    """
    if not op.swagger_spec.config['validate_responses']:
        return

    validate_response_body(op, response_spec, response)
    validate_response_headers(op, response_spec, response)


def validate_response_body(op, response_spec, response):
    """
    Validate an outgoing response's body against the response's Swagger
    specification.

    :type op: :class:`bravado_core.operation.Operation`
    :type response_spec: dict
    :type response: :class:`bravado_core.response.OutgoingResponse`
    :raises: SwaggerMappingError
    """
    # response that returns nothing in the body
    response_body_spec = response_spec.get('schema')
    if response_body_spec is None:
        if response.text in EMPTY_BODIES:
            return
        raise SwaggerMappingError(
            "Response body should be empty: {0}".format(response.text))

    if response.content_type not in op.produces:
        raise SwaggerMappingError(
            "Response content-type '{0}' is not supported by the Swagger "
            "specification's content-types '{1}"
            .format(response.content_type, op.produces))

    if response.content_type == APP_JSON:
        response_value = response.json()
        validate_schema_object(
            op.swagger_spec, response_body_spec, response_value)
    else:
        # TODO: Expand content-type support for non-json types
        raise SwaggerMappingError(
            "Unsupported content-type in response: {0}"
            .format(response.content_type))


def validate_response_headers(op, response_spec, response):
    """
    Validate an outgoing response's headers against the response's Swagger
    specification.

    :type op: :class:`bravado_core.operation.Operation`
    :type response_spec: dict
    :type response: :class:`bravado_core.response.OutgoingResponse`
    """
    headers_spec = response_spec.get('headers')
    if not headers_spec:
        return

    for header_name, header_spec in iteritems(headers_spec):
        validate_schema_object(
            op.swagger_spec, header_spec, response.headers.get(header_name))
