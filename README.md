# CerealBox for Python

CerealBox is a blazingly fast Zero Dependency generic Serializer / Deserializer for python dictionaries. It has an
extendable architecture that allows custom serializers to be built through config. The module also includes built in
implementations of serializing common data types to a JSON compatible dictionary or DynamoDB JSON.

## Getting started

### Install the module

Using poetry

```
poetry add cerealbox
```

or using pip

```
pip install cerealbox
```

### Using the built-in serializers

#### jsonable

The jsonable serializer converts any input dict or value into JSON serializable output value.

```python
from cerealbox.jsonable import as_jsonable
from decimal import Decimal
from enum import Enum
from datetime import datetime


class Country(Enum):
    ZA = 'South Africa'
    AU = 'Australia'
    US = 'United States'


sample_input = {
    "name": "Jane",
    "age": 23,
    "balance": Decimal('250.10'),
    "country": Country.ZA,
    "updated_at": datetime(2020, 1, 1)
}

print(as_jsonable(sample_input))
# {'name': 'Jane', 'age': 23, 'balance': '250.10', 'country': 'South Africa', 'updated_at': '2020-01-01T00:00:00'}

# You can also use as_jsonable as the default function to json.dumps 
import json

print(json.dumps(sample_input, default=as_jsonable, indent=4))
# {
#     "name": "Jane",
#     "age": 23,
#     "balance": "250.10",
#     "country": "South Africa",
#     "updated_at": "2020-01-01T00:00:00"
# }
```

The default encoders for `as_jsonable` are as follows:

```
     | Python            | JSONABLE        |
     +===================+=================+
     | dict              | dict            |
     | list, tuple       | list            |
     | set               | list            |
     | string            | string          |
     | int, float        | int, float      |
     | bool              | bool            |
     | None              | None            |
     | Decimal           | string          |
     | datetime          | string (iso)    |
     | enum              | string (value)  |
     | uuid              | string          |
```

#### DynamoDB

The DynamoDB Serializer/Deserializer is capable of transforming python values into DynamoDB JSON and back. It supports
most common data types. Some transformations are not reversible (eg converting a datetime to a string). This limitation
is due to cerealbox being schemaless, and can be overcome by using a module such as `typed-models` or `pydantic`

```python
from cerealbox.dynamo import from_dynamodb_json, as_dynamodb_json
from decimal import Decimal
from enum import Enum
from datetime import datetime
from pprint import pprint


class Country(Enum):
    ZA = 'South Africa'
    AU = 'Australia'
    US = 'United States'


sample_input = {
    "name": "Jane",
    "age": 23,
    "balance": Decimal('250.10'),
    "country": Country.ZA,
    "updated_at": datetime(2020, 1, 1)
}

ddb_json = as_dynamodb_json(sample_input)
pprint(ddb_json)
# {'M': {'age': {'N': '23'},
#        'balance': {'N': '250.10'},
#        'country': {'S': 'South Africa'},
#        'name': {'S': 'Jane'},
#        'updated_at': {'S': '2020-01-01T00:00:00'}}}

# Reversing the operation

pprint(from_dynamodb_json(ddb_json))

# {'age': Decimal('23'),
#  'balance': Decimal('250.10'),
#  'country': 'South Africa',
#  'name': 'Jane',
#  'updated_at': '2020-01-01T00:00:00'}
```

When serializing from a dictionary to DynamoDB JSON, the following mapping is used:

```
   Python                                  DynamoDB
   ------                                  --------
   None                                    {'NULL': True}
   True/False                              {'BOOL': True/False}
   int/Decimal                             {'N': str(value)}
   string                                  {'S': string}
   Binary/bytearray/bytes (py3 only)       {'B': bytes}
   set([int/Decimal])                      {'NS': [str(value)]}
   set([string])                           {'SS': [string])
   set([Binary/bytearray/bytes])           {'BS': [bytes]}
   list                                    {'L': list}
   dict                                    {'M': dict}
   float                                   {'S': str(value)}
   datetime/date/time                      {'S': str(value.isoformat())}
   Enum                                    {'S': str(value.value)}
   UUID                                    {'S': str(value)}
```

When serializing from DynamoDB JSON to a Python dict, the following mapping is used:

```
   DynamoDB                                Python
   --------                                ------
   {'NULL': True}                          None
   {'BOOL': True/False}                    True/False
   {'N': str(value)}                       Decimal(str(value))
   {'S': string}                           string
   {'B': bytes}                            Binary(bytes)
   {'NS': [str(value)]}                    set([Decimal(str(value))])
   {'SS': [string]}                        set([string])
   {'BS': [bytes]}                         set([bytes])
   {'L': list}                             list
   {'M': dict}                             dict
```

### Writing your own serializer

A serializer is made up of a dict that maps each datatype to a function that produces its serialized version. There are
3 special cases for these functions:

1. If the type and the mapped function are the same (eg `{str: str}`), the value is not modified during serialization.
   This is a performance optimization.
2. Dealing with the value `None` is a special case, since `type(None)` is `NoneType`. If you would like to handle `None`
   , import `NoneType` from cerealbox and use it as the type
3. If a type maps to a function that accepts a parameter named `serialize`, an instance of the serializer is passed
   along with the function. This allows recursive calls to deal with items inside of dictionaries, lists etc.

Example use case:
-
> When serializing a dict, convert all Decimal types to a String with the prefix `$ `. Redact any string that contains the word "classified". Handle nested items inside of a list in a similar manner

```python
from cerealbox import Cereal
from decimal import Decimal
from pprint import pprint


def redact_strings(value):
    if 'classified' in value.lower():
        return "***classified***"

    return value


def serialize_list(value, serialize):
    return [serialize(item) for item in value]


ENCODERS = {
    str: redact_strings,
    Decimal: lambda num: f"$ {num}",
    list: serialize_list,
    dict: lambda v, serialize: {k_: serialize(v_) for k_, v_ in v.items()}
}

custom_serializer = Cereal(encoders=ENCODERS)

sample_input = {
    "name": "Jane",
    "assignment": "Eat Cereal. Mission is Classified",
    "funds": Decimal('1024.50'),
    "keywords": [Decimal('1.5'), "Hello, World", "I am classified."]
}

pprint(custom_serializer(sample_input))
# {'assignment': '***classified***',
#  'funds': '$ 1024.50',
#  'keywords': ['$ 1.5', 'Hello, World', '***classified***'],
#  'name': 'Jane'}
```

### Extending an existing serializer

> Extend jsonable to redact strings containing the word Classified

```python
from cerealbox.jsonable import as_jsonable


def redact_strings(value):
    if 'classified' in value.lower():
        return "***classified***"

    return value


as_jsonable.extend_encoders({str: redact_strings})

sample_input = {
    "name": "Jane",
    "age": 23,
    "mission": "[Classified] Divide by zero and see what happens.",
}

print(as_jsonable(sample_input))
# {'name': 'Jane', 'age': 23, 'mission': '***classified***'}
```

## DynamoDB JSON Serializer/Deserializer Benchmarks

**cerealbox** has crude benchmarks against [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) 
(using TypeSerializer and TypeDeserializer) and [dynamodb-json](https://github.com/Alonreznik/dynamodb-json). The
benchmark calculates the roundtrip conversion from a python dict to DynamoDB JSON and back to a python dict. See `./benchmarks`

| package | version | relative performance | mean time |
| :---: | :---: | :---: | :---: |
| `cerealbox` | 0.1.2 | - | 102.4 uS |
| `boto3` | 1.18.30 | 2.69x slower | 275.2 uS |
| `dynamodb-json` | 1.3 | 7.36x slower | 754.0 uS |

## Contributing

To work on the cerealbox codebase, you'll want to clone the project locally and install the required dependencies
via [poetry](https://poetry.eustace.io).

```bash
git clone git@github.com:a2d24/cerealbox.git
```
