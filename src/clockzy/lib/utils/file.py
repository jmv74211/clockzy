"""Utils functions related with files"""
import json


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
