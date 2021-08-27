import pytest

from cerealbox.cereal import Cereal


def test_required_positional_arg_encoders():
    with pytest.raises(TypeError) as ex_info:
        cereal = Cereal()

    assert 'positional argument' in ex_info.value.args[0]
    assert 'encoders' in ex_info.value.args[0]


def test_custom_encoder():
    encoders = {
        str: str,
        int: lambda i: i + 10,
    }

    serialize = Cereal(encoders)

    assert serialize('Test') == 'Test'
    assert serialize(20) == 30


def test_recursive_serializer():
    encoders = {
        str: str,
        int: lambda i: i + 10,
        dict: lambda v, serialize: {k_: serialize(v_) for k_, v_ in v.items()}
    }
    serialize = Cereal(encoders)

    assert serialize({'name': 'Jack', 'age': 20}) == {'name': 'Jack', 'age': 30}


def test_unable_to_serialize():
    encoders = {}
    serialize = Cereal(encoders)

    with pytest.raises(TypeError) as ex_info:
        serialize(1)

    assert ex_info.value.args[0] == 'Unable to serialize value 1 of type int'


