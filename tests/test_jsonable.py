import datetime
from decimal import Decimal
from enum import Enum
from uuid import uuid4

from cerealbox.jsonable import as_jsonable


class Gender(Enum):
    MALE = 'Male'
    FEMALE = 'Female'


sample_date = datetime.datetime(2020, 1, 1, 0, 0, 0, 0)
sample_uuid = uuid4()


def test_bool():
    assert as_jsonable(True) == True


def test_float():
    assert as_jsonable(1.0) == 1.0


def test_int():
    assert as_jsonable(42) == 42


def test_str():
    assert as_jsonable("Hello") == "Hello"


def test_set():
    assert as_jsonable({1, 2, 3}) == [1, 2, 3]


def test_none():
    assert as_jsonable(None) is None


def test_decimal():
    assert as_jsonable(Decimal('1.2')) == '1.2'


def test_dict():
    assert as_jsonable({'a': 1, 'b': Decimal(2)}) == {'a': 1, 'b': '2'}


def test_list():
    assert as_jsonable([1, Decimal('2'), sample_date]) == [1, "2", '2020-01-01T00:00:00']


def test_uuid():
    assert as_jsonable(sample_uuid) == str(sample_uuid)


def test_enum():
    assert as_jsonable(Gender.MALE) == "Male"

def test_tuple():
    assert as_jsonable((1,2)) == [1,2]