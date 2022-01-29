"""Utils functions related with files"""
import json
import yaml


def read_json(file_path):
    """
    Read a JSON file from a given path, return a dictionary with the json data.
    Args:
        file_path (str): Path of the JSON file to be read.
    Returns:
        output(dict): Read json data.
    """
    with open(file_path, 'r') as f:
        output = json.loads(f.read())

    return output


def read_yaml(file_path):
    """Get the data from a YAML file.

    Args:
        file_path (str): YAML file path.

    Returns:
       dict: Yaml data.
    """
    with open(file_path) as f:
        return yaml.safe_load(f)
