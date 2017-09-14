"""
The CoRR http adapter serves as a connection to CoRR and provides a glossary
of functions that can be used to interact with CoRR. These includes things like
creating new projects and records.

Note: This is a prototype.
"""
import os
import logging

import json

from maestrowf.plugins.archive.abstract.httpadapter import HttpAdapter
from maestrowf.plugins.archive import utils

LOGGER = logging.getLogger(__name__)

class CorrHttpAdapter(HttpAdapter):
    """
    Adatper for sending Maestro specification data to CoRR. This implementation
    is based on:
    https://github.com/usnistgov/corr-sumatra/blob/corr-integrate/sumatra/recordstore/http_store.py#L231
    """
    def __init__(self, config_path, disable_ssl_certificate_validation=True):
        super(CorrHttpAdapter, self).__init__(disable_ssl_certificate_validation)
        self.server_url = self.load_config(config_path)

    def create_project(self, spec_path):
        """
        Creates a new project in CoRR with the given Maestro
        specificiation path.

        :param spec_path: The maestro spec path to use for the new project.
        :returns: A tuple containing the HTTP response and content.
        """
        LOGGER.debug('Creating a new project with spec at: {}'\
            ''.format(spec_path))
        # Extract the yaml data
        yaml_data = utils.read_yaml(spec_path)
        _content = {}
        _content['name'] = yaml_data['description']['name']
        _content['description'] = yaml_data['description']['description']
        url = '{}project/create'.format(self.server_url)

        response, content = self._post(url, _content)
        self._check_response_content(url=url, response=response,
                    content=content, response_code=200, content_code=201)
        return response, content

    def update_project(self, spec_path):
        """
        Updates a project in CoRR with the given Maestro specificiation path.

        :param spec_path: The maestro spec path to use for the project.
        :returns: A tuple containing the HTTP response and content.
        """
        LOGGER.debug('Updating project with spec at: {}'\
            ''.format(spec_path))
        # Extract the yaml data
        yaml_data = utils.read_yaml(spec_path)
        _content = {}
        _content['name'] = yaml_data['description']['name']
        _content['description'] = yaml_data['description']['description']

        # Check if project exists to update
        project = self.has_project(_content['name'])
        if not project:
            msg = ('No project exists with the name: {}'\
                ''.format(_content['name']))
            LOGGER.exception(msg)
            raise ValueError(msg)

        # Update the project
        url = '{}project/update/{}'.format(self.server_url, project['id'])
        response, content = self._post(url, _content)
        self._check_response_content(url=url, response=response,
                    content=content, response_code=200, content_code=201)
        return response, content

    def has_project(self, project_name):
        """
        Check to see if an existing project exists with the given project name.

        :param project_name: The project name to check for.
        :returns: The project if it exists, None if it doesn't.
        """
        LOGGER.debug('Checking if project <{}> exists.'.format(project_name))
        project = None
        url = "%sprojects" % (self.server_url)
        response, content = self._get(url)
        self._check_response_content(url=url, response=response,
                        content=content, response_code=200, content_code=200)
        result = json.loads(content)
        for p in result['content']['projects']:
            if p['name'] == project_name:
                project = p
                break
        return project

    def create_record(self, project_name, corr_spec_path):
        """
        Create a record with the corresponding project name in CoRR. If the
        project does not exist, will create the project and then insert the
        record.

        :param project_name: The project name to use for the record.
        :param corr_spec_path: The path to the CoRR spec to store.
        :raises ValueError: If given an incorrect project name.
        :returns: A tuple containing the HTTP response and content.
        """
        LOGGER.debug('Inserting new record into project: {}\n'\
            'with spec: {}'.format(project_name, corr_spec_path))
        project = None
        project = self.has_project(project_name=project_name)
        if not project:
            msg = 'Project <{}> does not exist. Cannot add record.'
            LOGGER.error(msg)
            raise ValueError(msg)
        # Create the record
        record = utils.read_yaml(corr_spec_path)
        url = '{}project/record/create/{}'.format(self.server_url,
            project['id'])
        response, content = self._post(url, record)
        self._check_response_content(url=url, response=response,
                        content=content, response_code=200, content_code=201)
        return response, content

    def update_record(self, project_name, record_id, corr_spec_path):
        """
        Update the record with the corresponding project name and record id in
        CoRR.

        :param project_name: The project name to use for the record update.
        :param corr_spec_path: The path to the CoRR spec to store.
        :returns: A tuple containing the HTTP response and content.
        """
        LOGGER.debug('Updating record: <{}>\n of project: {}\n'\
           'with spec: {}'.format(record_id, project_name, corr_spec_path))
        record = utils.read_yaml(corr_spec_path)
        url = "%srecord/update/%s" % (self.server_url, record_id)
        response, content = self._post(url, record)
        self._check_response_content(url=url, response=response,
                        content=content, response_code=200, content_code=201)
        record_payload = json.loads(content)
        return response, content

    def load_config(self, config_path):
        """
        Loads the json config file for the CoRR archive adapter.

        :param config_path: The path to the json configuration file.
        :returns: The configured URL to use for CoRR.
        """
        LOGGER.debug('Loading config file: {}'.format(config_path))
        config = utils.read_json(config_path)

        scope = config.get('default', {})
        api = scope.get('api',{})
        host = api.get('host','')
        port = api.get('port', 80)
        key = api.get('key', '')
        path = api.get('path', '')
        token = scope.get('app', '')
        url ='{0}:{1}{2}/private/{3}/{4}/'\
            ''.format(host, port, path, key, token)
        return url
