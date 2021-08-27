import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Dict, Type
from uuid import UUID

from .cereal import Cereal, NoneType


def serialize_dict(v, serialize):
    return {
        k_: serialize(v_)
        for k_, v_ in v.items()
    }


def serialize_list(v, serialize):
    return [serialize(item) for item in v]

#     | Python            | JSONABLE        |
#     +===================+=================+
#     | dict              | dict            |
#     | list, tuple       | list            |
#     | set               | list            |
#     | string            | string          |
#     | int, float        | int, float      |
#     | bool              | bool            |
#     | None              | None            |
#     | Decimal           | string          |
#     | datetime          | string (iso)    |
#     | enum              | string (value)  |
#     | uuid              | string          |

JSONABLE_ENCODERS: Dict[Type[Any], Callable[[Any], Any]] = {
    bool: bool,
    str: str,
    int: int,
    float: float,
    NoneType: NoneType,

    list: serialize_list,
    set: serialize_list,
    dict: serialize_dict,
    tuple: serialize_list,

    Decimal: str,
    datetime.date: lambda d: d.isoformat(),
    datetime.datetime: lambda d: d.isoformat(),
    datetime.time: lambda d: d.isoformat(),
    datetime.timedelta: lambda td: td.total_seconds(),
    Enum: lambda o: o.value,
    UUID: str
}

as_jsonable = Cereal(encoders=JSONABLE_ENCODERS)

__all__ = ['as_jsonable']
