import datetime
from collections.abc import Set
from decimal import Decimal
from enum import Enum
from typing import Dict, Callable, Any, Type
from uuid import UUID

from .cereal import Cereal, NoneType


def serialize_dict(v, serialize):
    return {
        'M': {
            k_: serialize(v_)
            for k_, v_ in v.items()
        }
    }


def serialize_list(v, serialize):
    return {'L': [serialize(item) for item in v]}


def serialize_set(v):
    if all(isinstance(item, (int, float, Decimal)) for item in v):
        return {'NS': [str(item) for item in v]}
    elif all(isinstance(item, str) for item in v):
        return {'SS': [str(item) for item in v]}
    elif all(isinstance(item, (bytearray, bytes)) for item in v):
        return {'BS': [item if isinstance(item, bytes) else bytearray(item) for item in v]}

    raise TypeError("All values in a set must be of the same family of types (numbers, strings or bytes)")


serialize_as_string = lambda v: {'S': str(v)}
serialize_as_number = lambda v: {'N': str(v)}

#   Python                                  DynamoDB
#   ------                                  --------
#   None                                    {'NULL': True}
#   True/False                              {'BOOL': True/False}
#   int/Decimal                             {'N': str(value)}
#   string                                  {'S': string}
#   Binary/bytearray/bytes (py3 only)       {'B': bytes}
#   set([int/Decimal])                      {'NS': [str(value)]}
#   set([string])                           {'SS': [string])
#   set([Binary/bytearray/bytes])           {'BS': [bytes]}
#   list/tuple                              {'L': list}
#   dict                                    {'M': dict}
#   float                                   {'S': str(value)}
#   datetime/date/time                      {'S': str(value.isoformat())}
#   Enum                                    {'S': str(value.value)}
#   UUID                                    {'S': str(value)}


DYNAMODB_ENCODERS: Dict[Type[Any], Callable[[Any], Any]] = {
    bool: lambda v: {'BOOL': v},
    str: serialize_as_string,
    int: serialize_as_number,
    float: serialize_as_number,
    NoneType: lambda v: {'NULL': True},

    list: serialize_list,
    tuple: serialize_list,
    dict: serialize_dict,
    set: serialize_set,
    Set: serialize_set,

    bytes: lambda b: {'B': b},
    bytearray: lambda ba: {'B': bytes(ba)},
    Decimal: serialize_as_number,

    datetime.date: lambda d: serialize_as_string(d.isoformat()),
    datetime.datetime: lambda d: serialize_as_string(d.isoformat()),
    datetime.time: lambda d: serialize_as_string(d.isoformat()),
    datetime.timedelta: lambda td: serialize_as_number(td.total_seconds()),
    Enum: lambda o: serialize_as_string(o.value),
    UUID: serialize_as_string,
}

#   DynamoDB                                Python
#   --------                                ------
#   {'NULL': True}                          None
#   {'BOOL': True/False}                    True/False
#   {'N': str(value)}                       Decimal(str(value))
#   {'S': string}                           string
#   {'B': bytes}                            Binary(bytes)
#   {'NS': [str(value)]}                    set([Decimal(str(value))])
#   {'SS': [string]}                        set([string])
#   {'BS': [bytes]}                         set([bytes])
#   {'L': list}                             list
#   {'M': dict}                             dict

DYNAMODB_TYPES = {
    'NULL': lambda v, serialize: None,
    'BOOL': lambda v, serialize: v,
    'N': lambda v, serialize: Decimal(v),
    'S': lambda v, serialize: v,
    'B': lambda v, serialize: v,
    'NS': lambda v, serialize: set(Decimal(item) for item in v),
    'SS': lambda v, serialize: set(v),
    'BS': lambda v, serialize: set(v),
    'L': lambda v, serialize: [serialize(item) for item in v],
    'M': lambda v, serialize: {k_: serialize(v_) for k_, v_ in v.items()}
}

def decode_dynamodb_primative(value):
    _type = next(iter(value))

    if _type not in DYNAMODB_TYPES:
        raise TypeError(f'DynamoDB does not have a type {_type}. Use one of {list(DYNAMODB_TYPES.keys())}')

    return DYNAMODB_TYPES[_type](value[_type], decode_dynamodb_primative)


def decode_dynamodb_json(v):

    key = next(iter(v))
    # Convert root level attribute map into {"M": ...}
    if len(v) > 1 or (len(v) == 1 and key not in DYNAMODB_TYPES):
        v = {'M': v}

    return decode_dynamodb_primative(v)




# A dynamodb json value is always a dict, hence there is only one decoder that proxies the conversion for all types
DYNAMODB_DECODERS = {
    dict: decode_dynamodb_json
}

as_dynamodb_json = Cereal(encoders=DYNAMODB_ENCODERS)
from_dynamodb_json = Cereal(encoders=DYNAMODB_DECODERS)

__all__ = ['as_dynamodb_json', 'from_dynamodb_json']
