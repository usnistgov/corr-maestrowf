
import logging
import os
import yaml

from maestrowf.plugins.archive.interfaces.corrhttpadapter import CorrHttpAdapter
from maestrowf.plugins.archive.transformers import corrhttptransformer
from maestrowf.plugins.archive import utils

ADAPTERS = {'corrhttp': CorrHttpAdapter}

LOGGER = logging.getLogger(__name__)

class Director(object):
    """
    The archive director directs the Maestro workflow to the specified archive
    adapter and calls the necessary adapter functions to archive the workflow.
    """
    def __init__(self, adapter, config_path):
        LOGGER.debug('Generating new Archive Director with adapter: {}\n and '
            'config path: {}'.format(adapter, config_path))
        self.adapter = adapter
        self.archive_adapter_type = ADAPTERS[adapter]
        self.archive_adapter = self.archive_adapter_type(config_path=config_path)

    def archive(self, spec_path):
        """
        Takes a Maestro specification file path and archives it.

        :param spec_path: The file path to the Maestro spec.
        :raises ValueError: If the Director has no supported adapter in use.
        """
        LOGGER.info('Archiving spec: {}'.format(spec_path))
        LOGGER.debug('With adapter: {}'.format(self.archive_adapter._type()))

        if self.adapter == 'corrhttp':
            self.archive_corrhttp(spec_path=spec_path)
        else:
            # Shouldn't get here but this is for default.
            msg = 'Unsupported archive adapter: <{}>'.format(str(self.adapter))
            LOGGER.error(msg)
            raise ValueError(msg)

    def archive_corrhttp(self, spec_path):
        """
        Takes a Maestro specification file path and archives it to CoRR over
        HTTP.

        :param spec_path: The file path to the Maestro spec.
        """
        LOGGER.debug('Generating CoRR spec.')

        # Grab spec name. Split on '.' to remove file extension.
        archive_output_name = '{}-archive.yaml'.format(
                            utils.get_file_name(spec_path).rsplit('.', 1)[0])
        archive_output_path = os.path.dirname(os.path.realpath(spec_path))
        # TODO Create real package for transformer instead of script coupled to corr
        archive_yaml_path, archive_yaml_content = corrhttptransformer.main(
                                                corr_output=archive_output_name,
                                                output_path=archive_output_path,
                                                maestro_spec_path=spec_path)
        LOGGER.debug('Transform path: {}\nTransform content: {}'
            ''.format(archive_output_path, archive_yaml_path))
        # Create project if needed
        try:
            response, content = self.archive_adapter.create_project(spec_path)
        except ValueError as e:
            LOGGER.exception('Project already created. Cannot add again.')
        # Create record
        yaml_data = utils.read_yaml(spec_path)
        project_name = yaml_data['description']['name']
        self.archive_adapter.create_record(project_name, archive_yaml_path)
