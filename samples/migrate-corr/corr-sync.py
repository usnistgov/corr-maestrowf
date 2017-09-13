"""Script to migrate a Maestrowf YAML file to a CoRR YAML file

To run use:

    $ python corr-sync.py --corr-output=corr.yaml --output-path=demo/sample_output

To run the tests:

    $ py.test --doctest-modules migrate_yaml.py

Test reading a sample Maestorwf file

>>> data_path = os.path.join(get_path(), 'lulesh_sample1.yaml')
>>> test_path = os.path.join(get_path(), 'corr-test.yaml')
>>> assert mapping(read_yaml(data_path)) == read_yaml(test_path)

"""

import os

# pylint: disable=redefined-builtin
from toolz.curried import pipe, get, curry, map, filter, tail, do
import yaml
import glob
import mimetypes
import click
import sys
from logic import HttpCoRRStore


def file_metadata(path):
    """Generate metadata for one file

    >>> from click.testing import CliRunner
    >>> with CliRunner().isolated_filesystem() as dir_:
    ...     test_file = os.path.join(dir_, 'hello.json')
    ...     with open(test_file, 'w') as f:
    ...         _ = f.write('{"hello": "hello"}')
    ...     metadata = file_metadata(test_file)
    >>> assert('hello.json' in metadata['path'])
    >>> assert metadata['metadata'] == {'encoding': 'utf-8',
    ...                                 'mimetype': 'application/json',
    ...                                 'size': 18}

    Args:
      path: the path to the file

    Returns:
      dictionary of metadata
    """
    return {
        'path': os.path.relpath(path),
        'metadata': {
            'encoding': 'utf-8',
            'mimetype': mimetypes.guess_type(path)[0],
            'size': os.path.getsize(path)
        }
    }


def glob_all_files_2(path):
    """Find all files in Py 2.7
    """
    import fnmatch

    matches = []
    for root, dirnames, filenames in os.walk(path):
        for filename in fnmatch.filter(filenames, '*'):
            matches.append(os.path.join(root, filename))

    return matches


def glob_all_files_3(path):
    """Find all files

    Args:
      path: the path to search for files

    Returns:
      a list of files
    """
    return pipe(
        os.path.join(path, '**'),
        lambda x: glob.glob(x, recursive=True),
        filter(os.path.isfile),
    )


def glob_all_files(path):
    if sys.version_info[0] < 3:
        return glob_all_files_2(path)
    else:
        return glob_all_files_3(path)


def outputs(path):
    """Generate outputs metadata based on path

    Args:
      path: the path to the output data

    Returns:
      a list of file metadata

    """

    return pipe(
        path,
        glob_all_files,
        map(file_metadata),
        list
    )


@curry
def mapping(output_path, data):
    """Map from Maestrowf data to CoRR data

    Args:
      data: the Maestrowf data
      output_path: the path to the output data

    Returns
      the CoRR data
    """
    return {
        'execution': {
            'parameters': data['global.parameters'],
            'cmd_line': data['study'][-1]['run']['cmd']},
        'system': {'env': data['env']},
        'outputs': outputs(output_path),
        'inputs': [],
        'dependencies': []
    }


def get_path():
    """Return the local file path for this file.

    Returns:
      the filepath
    """
    return pipe(
        __file__,
        os.path.realpath,
        os.path.split,
        get(0)
    )


def read_yaml(filepath):
    """Read a YAML file

    Args:
      filepath: the path to the YAML file

    Returns:
      returns a dictionary
    """
    with open(filepath) as stream:
        data = yaml.safe_load(stream)
    return data


@curry
def write_yaml_data(filepath, data):
    """Write data to YAML file

    Args:
      filepath: the path to the YAML file
      data: a dictionary to write to the YAML file

    """
    with open(filepath, 'w') as stream:
        yaml.safe_dump(data, stream, default_flow_style=False, indent=2)
    return (filepath, data)


def find_yaml_file(path):
    """Find a YAML file in the path

    Args:
      path: find a YAML file on the path

    Returns:
      the path to the YAML file
    """
    return pipe(
        path,
        glob_all_files,
        filter(lambda x: tail(5, x) == '.yaml'),
        list,
        get(0)
    )


@curry
def upload(config, project_name, data):
    store = HttpCoRRStore(server_url=config)
    # store.get_project(project_name=project_name)
    store.create_record(project_name=project_name,
                        record=data)


@click.command()
@click.option('--corr-output',
              'corr_output',
              required=True,
              default='corr.yaml',
              help="Set the CoRR YAML file")
@click.option('--output-path',
              'output_path',
              required=True,
              help="Path the Maestro outputs")
@click.option('--config-path',
              'config_path',
              required=True,
              help="CoRR config file path")
@click.option('--project-name',
              'project_name',
              required=True,
              help="Set the project name")
def main(corr_output, output_path, config_path, project_name):
    """Read in a Maestrowf YAML, translate and write the CoRR YAML
    """
    return pipe(
        output_path,
        find_yaml_file,
        read_yaml,
        mapping(output_path),
        do(upload(config_path, project_name)),
        write_yaml_data(corr_output)
    )


if __name__ == '__main__':
    # data = main()
    main()
