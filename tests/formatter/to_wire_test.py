from datetime import datetime, date

from mock import patch
import six

from bravado_core.formatter import to_wire


def test_none(minimal_swagger_spec):
    string_spec = {'type': 'string', 'format': 'date'}
    assert to_wire(minimal_swagger_spec, string_spec, None) is None


def test_no_format_returns_value(minimal_swagger_spec):
    string_spec = {'type': 'string'}
    assert 'boo' == to_wire(minimal_swagger_spec, string_spec, 'boo')


def test_date(minimal_swagger_spec):
    string_spec = {'type': 'string', 'format': 'date'}
    assert '2015-04-01' == to_wire(
        minimal_swagger_spec, string_spec, date(2015, 4, 1))


def test_datetime(minimal_swagger_spec):
    string_spec = {'type': 'string', 'format': 'date-time'}
    assert '2015-03-22T13:19:54' == to_wire(
        minimal_swagger_spec, string_spec, datetime(2015, 3, 22, 13, 19, 54))


@patch('bravado_core.spec.warnings.warn')
def test_no_registered_format_returns_value_as_is(
        mock_warn, minimal_swagger_spec):
    string_spec = {'type': 'string', 'format': 'bar'}
    assert 'baz' == to_wire(minimal_swagger_spec, string_spec, 'baz')
    assert mock_warn.call_count == 1


def test_int64_long(minimal_swagger_spec):
    integer_spec = {'type': 'integer', 'format': 'int64'}
    if six.PY3:
        result = to_wire(minimal_swagger_spec, integer_spec, 999)
        assert 999 == result
        assert isinstance(result, int)
    else:
        result = to_wire(minimal_swagger_spec, integer_spec, long(999))
        assert long(999) == result
        assert isinstance(result, long)


def test_int64_int(minimal_swagger_spec):
    integer_spec = {'type': 'integer', 'format': 'int64'}
    result = to_wire(minimal_swagger_spec, integer_spec, 999)
    if six.PY3:
        assert 999 == result
        assert isinstance(result, int)
    else:
        assert long(999) == result
        assert isinstance(result, long)


def test_int32_long(minimal_swagger_spec):
    if six.PY3:  # test irrelevant in py3
        return
    integer_spec = {'type': 'integer', 'format': 'int32'}
    result = to_wire(minimal_swagger_spec, integer_spec, long(999))
    assert 999 == result
    assert isinstance(result, int)


def test_int32_int(minimal_swagger_spec):
    integer_spec = {'type': 'integer', 'format': 'int32'}
    result = to_wire(minimal_swagger_spec, integer_spec, 999)
    assert 999 == result
    assert isinstance(result, int)


def test_float(minimal_swagger_spec):
    number_spec = {'type': 'number', 'format': 'float'}
    result = to_wire(minimal_swagger_spec, number_spec, 3.14)
    assert 3.14 == result
    assert isinstance(result, float)


def test_double(minimal_swagger_spec):
    number_spec = {'type': 'number', 'format': 'double'}
    result = to_wire(minimal_swagger_spec, number_spec, 3.14)
    assert 3.14 == result
    assert isinstance(result, float)


def test_byte_string(minimal_swagger_spec):
    string_spec = {'type': 'string', 'format': 'byte'}
    result = to_wire(minimal_swagger_spec, string_spec, 'x')
    assert 'x' == result
    assert isinstance(result, str)


def test_byte_unicode(minimal_swagger_spec):
    string_spec = {'type': 'string', 'format': 'byte'}
    result = to_wire(minimal_swagger_spec, string_spec, u'x')
    assert 'x' == result
    assert isinstance(result, str)
