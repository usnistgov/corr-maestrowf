import yaml
import ntpath
import os
import logging
import json

LOGGER = logging.getLogger(__name__)

def read_yaml(filepath):
    """
    Read a YAML file and returns the corresponding dictionary.

    :param filepath: The path to the YAML file.
    :returns: A dictionary of the YAML file.
    """
    LOGGER.debug('Reading in YAML file: {}'.format(filepath))
    with open(filepath) as stream:
        data = yaml.safe_load(stream)
    return data

def read_json(filepath):
    """
    Read a JSON file and returns the corresponding dictionary.

    :param filepath: The path to the JSON file.
    :returns: A dictionary of the JSON file.
    """
    LOGGER.debug('Reading in JSON file: {}'.format(filepath))
    with open(filepath) as stream:
        data = json.load(stream)
    return data

def get_file_name(path):
    """
    Grabs the name of the file of the given path.

    Taken from https://stackoverflow.com/a/8384788.

    :param filepath: The filepath to get the name of.
    :returns: The file name.
    """
    LOGGER.debug('Getting file name of path: {}'.format(path))
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

def get_file_path(file_name):
    """
    Return the local file path for this file.

    :returns: The filepath.
    """
    LOGGER.debug('Getting file path of file: {}'.format(file_name))
    return os.path.abspath(file_name)
