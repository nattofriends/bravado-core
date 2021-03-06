from mock import patch

from bravado_core.spec import Spec


def assert_validate_call_count(expected_call_count, config, petstore_dict):
    spec = Spec(petstore_dict, config=config)
    with patch('bravado_core.spec.validator20.validate_spec') as m_validate:
        spec.build()
    assert expected_call_count == m_validate.call_count


def test_validate_swagger_spec(petstore_dict):
    assert_validate_call_count(
        1, {'validate_swagger_spec': True}, petstore_dict)


def test_dont_validate_swagger_spec(petstore_dict):
    assert_validate_call_count(
        0, {'validate_swagger_spec': False}, petstore_dict)
