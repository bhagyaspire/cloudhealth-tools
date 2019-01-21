import json
import yaml


def read_schema_file(file_path):
    with open(file_path) as schema_file:
        schema = json.load(schema_file)
    return schema


def read_spec_file(file_path):
    with open(file_path) as spec_file:
        spec = yaml.load(spec_file)
    return spec
