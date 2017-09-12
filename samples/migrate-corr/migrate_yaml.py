"""Script to migrate a Maestrowf YAML file to a CoRR YAML file

To run the tests:

    $ py.test --doctest-modules migrate_yaml.py

Test reading a sample Maestorwf file

>>> data_path = os.path.join(get_path(), 'lulesh_sample1.yaml')
>>> test_path = os.path.join(get_path(), 'corr-test.yaml')
>>> assert mapping(read_yaml(data_path)) == read_yaml(test_path)

"""

import os

# pylint: disable=redefined-builtin
from toolz.curried import pipe, get, curry, map, do, filter
import yaml
import glob
import mimetypes


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

    Retuns:
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


def outputs(path):
    """Generate outputs metadata based on path

    Args:
      path: the path to the output data

    Returns:
      a list of file metadata

    """
    return pipe(
        os.path.join(path, '**'),
        lambda x: glob.glob(x, recursive=True),
        filter(os.path.isfile),
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


def main(file_in, file_out, output_path):
    """Read in a Maestrowf YAML, translate and write a CoRR YAML

    Args:
      file_in: Maestrowf YAML path

    Returns:
      CoRR YAML path
    """
    return pipe(
        file_in,
        read_yaml,
        mapping(output_path),
        write_yaml_data(file_out)
    )


if __name__ == '__main__':
    main(
        os.path.join(get_path(), 'lulesh_sample1.yaml'),
        'corr-out.yaml',
        'sample_output'
    )
