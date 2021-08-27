import timeit
from decimal import Decimal
from pprint import pprint

from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from dynamodb_json import json_util

from cerealbox.dynamo import as_dynamodb_json, from_dynamodb_json

sample_object = {
    "name": "Jane",
    "gender": "Female",
    "age": 12,
    "allergies": {"Pollen", "Nuts"},
    "siblings": [
        {
            "name": "Jack",
            "gender": "Male",
            "allergies": None,
            "vehicles": {
                "count": 2,
                "items": [
                    {
                        "make": "Toyota",
                        "model": "86",
                        "year": 2013
                    },
                    {
                        "make": "BMW",
                        "model": "135i",
                        "year": 2015
                    }
                ]
            },
            "age": 33
        },
        {
            "name": "Jill",
            "gender": "Female",
            "allergies": None,
            "vehicles": {
                "count": 1,
                "items": [
                    {
                        "make": "Tesla",
                        "model": "Model S",
                        "year": 2020
                    }
                ]
            },
            "age": Decimal('25')
        }
    ]
}

boto_deserialize = TypeDeserializer().deserialize
boto_serialize = TypeSerializer().serialize


def benchmark_dynamodb_json():
    forwards = json_util.dumps(sample_object, as_dict=True)
    backwards = json_util.loads(forwards)
    return backwards


def benchmark_cerealbox():
    forwards = as_dynamodb_json(sample_object)
    backwards = from_dynamodb_json(forwards)
    return backwards


def benchmark_boto():
    forwards = boto_serialize(sample_object)
    backwards = boto_deserialize(forwards)
    return backwards


ITERATIONS = 10000

dynamodb_json_result = timeit.timeit(
    "benchmark_dynamodb_json()",
    setup="from __main__ import benchmark_dynamodb_json",
    number=ITERATIONS
)

boto_result = timeit.timeit(
    "benchmark_boto()",
    setup="from __main__ import benchmark_boto",
    number=ITERATIONS
)
cerealbox_result = timeit.timeit(
    "benchmark_cerealbox()",
    setup="from __main__ import benchmark_cerealbox",
    number=ITERATIONS
)

print("Output from each benchmark:")
print("\n  dynamodb-json:")
print("  --------------")
pprint(benchmark_dynamodb_json())
print("\n  boto3:")
print("  --------------")
pprint(benchmark_dynamodb_json())
print("\n  cerealbox:")
print("  --------------")
pprint(benchmark_dynamodb_json())
print()

factor_for_microseconds = 1 / ITERATIONS * 1000 * 1000
print(f"Time for roundtrip conversion of serialize / deserialize ({ITERATIONS} iteration average):")
print(f"  dynamodb-json:    {dynamodb_json_result * factor_for_microseconds} uS")
print(f"  boto3:            {boto_result * factor_for_microseconds} uS")
print(f"  cerealbox:        {cerealbox_result * factor_for_microseconds} uS")

# Time for roundtrip conversion of serialize / deserialize (10000 iteration average):
#   dynamodb-json:    754.0279692970216 uS
#   boto3:            275.22198479855433 uS
#   cerealbox:        102.44564969907515 uS
