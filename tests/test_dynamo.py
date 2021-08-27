import datetime
from decimal import Decimal

import pytest

from cerealbox.dynamo import as_dynamodb_json, from_dynamodb_json


@pytest.mark.parametrize("value, result", [
    (None, {'NULL': True}),
    (1, {'N': "1"}),
    (1.0, {'N': "1.0"}),
    (Decimal('0.3'), {'N': "0.3"}),
    (True, {'BOOL': True}),
    (False, {'BOOL': False}),
    ('Hello', {'S': 'Hello'}),
    (bytes('Hello', 'utf-8'), {'B': bytes('Hello', 'utf-8')}),
    (bytearray([2, 3, 5, 7]), {'B': bytes(bytearray([2, 3, 5, 7]))}),
    ([1, 2, 3], {'L': [{'N': '1'}, {'N': '2'}, {'N': '3'}]}),
    (['1', '2', 3], {'L': [{'S': '1'}, {'S': '2'}, {'N': '3'}]}),
    ({'a': 1, 'b': '2'}, {'M': {'a': {'N': '1'}, 'b': {'S': '2'}}})
])
def test_conversions(value, result):
    assert as_dynamodb_json(value) == result
    assert from_dynamodb_json(result) == value


@pytest.mark.parametrize("value, result", [
    ({1, 2}, {'NS': ['1', '2']}),
    ({'1', 'Hello'}, {'SS': ['1', 'Hello']}),
    ({bytes('Hello', 'utf-8'), bytes('World', 'utf-8')}, {'BS': [bytes('Hello', 'utf-8'), bytes('World', 'utf-8')]})
])
def test_set_conversions(value, result):
    assert set(from_dynamodb_json(result)) == set(value)
    assert set(from_dynamodb_json(as_dynamodb_json(value))) == set(value)

def test_tuple_conversion():
    assert as_dynamodb_json((1,2)) == {'L': [{'N': '1'}, {'N': '2'}]}

def test_bytearray_type():
    assert type(as_dynamodb_json(bytearray([2, 3, 5, 7]))['B']) == bytes
    assert type(as_dynamodb_json(bytes('Hello', 'utf-8'))['B']) == bytes


def test_datetime():
    sample_date = datetime.datetime(2020, 1, 1, 0, 0, 0, 0)
    assert as_dynamodb_json(sample_date) == {'S': "2020-01-01T00:00:00"}


def test_enum():
    from enum import Enum
    class Gender(Enum):
        MALE = 'Male'
        FEMALE = 'Female'

    assert as_dynamodb_json(Gender.FEMALE) == {'S': 'Female'}


def test_uuid():
    import uuid
    sample = uuid.uuid4()

    assert as_dynamodb_json(sample) == {'S': str(sample)}


def test_set_with_mixed_types():
    with pytest.raises(TypeError) as ex_info:
        as_dynamodb_json({1, "2"})

    assert ex_info.value.args[
               0] == "All values in a set must be of the same family of types (numbers, strings or bytes)"


def test_invalid_dynamodb_json():
    with pytest.raises(TypeError) as ex_info:
        from_dynamodb_json({"a": {"N": "1"}, "b": {'K': '1'}})

    assert str(ex_info.value.args[0]).startswith("DynamoDB does not have a type K. Use one of")


def test_with_and_without_map_type():
    assert from_dynamodb_json({"a": {"N": "1"}}) == from_dynamodb_json({"M": {"a": {"N": "1"}}})
