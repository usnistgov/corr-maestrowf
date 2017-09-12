"""
The CoRR archive adapter transforms the Maestro workflow specification to the
CoRR data schema to archive Maestro runs.

Note: This is a prototype.
"""
import os
import logging
import httplib2
import json

from maestrowf.abstracts.interfaces.archiveadapter import ArchiveAdapter
from maestrowf.interfaces.archive import utils

LOGGER = logging.getLogger(__name__)

class CorrHttpAdapter(ArchiveAdapter):
    """
    Adatper for sending Maestro specification data to CoRR. This implementation
    is based on:
    https://github.com/usnistgov/corr-sumatra/blob/corr-integrate/sumatra/recordstore/http_store.py#L231
    """
    def __init__(self, server_url, disable_ssl_certificate_validation=True):
        if 'http' in server_url:
            self.server_url = server_url
        else:

            # TODO Move these variables to the spec
            #scope = config.get('default', {})
            #api = scope.get('api',{})
            host = "http://10.0.1.119"
            port = "5100"
            key = "3dc30596c134871dbc646a338c3a82b2dfdbbd310c80b803fec74ae8a557e300"
            path = "/corr/api/v0.1"
            token =  "032356f8d58ae905b2128107d84726d7991cc1d27338d129fc55a2ed58177c1a"
            self.server_url = "{0}:{1}{2}/private/{3}/{4}/".format(host, port,
                path, key, token)
        self.client = httplib2.Http('.cache',
            disable_ssl_certificate_validation=disable_ssl_certificate_validation)

    def _get(self, url):
        """
        Executes a HTTP Get on the given URL.

        :param url: The url to perform the HTTP Get on.
        :returns: A tuple containing the HTTP response and content.
        """
        LOGGER.debug('Performing HTTPGet on: {}'.format(url))
        headers = {'Accept': 'application/json'}
        response, content = self.client.request(url, headers=headers)
        return response, content

    def _post(self, url, content):
        """
        Executes a HTTP Post on the given URL.

        :param url: The url to perform the HTTP Get on.
        :param content: The content to POST with.
        :returns: A tuple containing the HTTP response and content.
        """
        LOGGER.debug('Performing HTTPPost on: {}\nwith content: {}'\
            ''.format(url, content))
        headers = {'Content-Type': 'application/json'}
        response, content = self.client.request(url, 'POST',
                                                json.dumps(content),
                                                headers=headers)
        return response, content

    def create_project(self, spec_path):
        """
        Will attempt to create a new project in CoRR with the given
        Maestro specificiation path.

        :param spec_path: The maestro spec_path to use for the new project.
        :returns: A tuple containing the HTTP response and content.
        """
        LOGGER.debug('Creating a new project with spec at: {}'\
            ''.format(spec_path))

        # Extract the yaml data
        yaml_data = utils.read_yaml(spec_path)
        _content = {}
        _content['name'] = yaml_data['description']['name']
        _content['description'] = yaml_data['description']['description']
        url = "%sproject/create" % (self.server_url)

        response, content = self._post(url, _content)
        self._check_response_content(url=url, response=response,
                        content=content, response_code=200, content_code=201)

    def update_project(self, spec_path):
        """
        Update a project in CoRR with the given Maestro specificiation path.

        :param spec_path: The spec_path to use for the project.
        :returns: A tuple containing the HTTP response and content.
        """
        raise NotImplementedError

    def has_project(self, project_name):
        """
        Check to see if an existing project exists with the given project name.

        :param project_name: The project name to check for.
        :returns: True if the project exists, False otherwise.
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
        if project:
            return True
        else:
            return False

    def create_record(self, project_name, corr_spec_path):
        """
        Create the record to the corresponding project name in CoRR. If the
        project does not exist, will create the project and then insert the
        record.

        :param project_name: The project name to use for the record.
        :param corr_spec_path: The path to the CoRR spec path to store.
        :returns: A tuple containing the HTTP response and content.
        """
        LOGGER.debug('Inserting new record into project: {}'\
            ''.format(project_name))
        record_id = None
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
        if project is None:
            LOGGER.debug('Project <{}> does not exist. Creating new project.'\
                ''.format(project_name))
            response, content = self.create_project(project_name)
            project = json.loads(content)['content']

        record = utils.read_yaml(corr_spec_path)
        url = "%sproject/record/create/%s" % (self.server_url, project['id'])
        headers = {'Content-Type': 'application/json'}
        response, content = self._post(url, record)
        self._check_response_content(url=url, response=response,
                        content=content, response_code=200, content_code=201)
        return response, content

    def _check_response_content(cls, url, response, content, response_code=200,
                                content_code=200):
        """
        Used to check if the response code and the content code match the given
        codes.

        :param url: The URL used for the HTTP request.
        :param response: An HTTP Response to check.
        :param content: An HTTP content to check.
        :param response_code: The response code to check response against.
            Default 200.
        :param content_code: The content code to check content against. Default
            200.
        """
        LOGGER.debug('Checking response and content codes.')
        if response.status != response_code:
            msg = ('URL <{}> provided bad response status: {}\nContent: {}'\
                ''.format(url, response.status, content))
            LOGGER.exception(msg)
            raise StandardError(msg)
        else:
            code = json.loads(content)['code']
            if code != content_code:
                msg = ('URL <{}> provided bad content code status: {}\n'\
                    'Content: {}'.format(response.status, content))
                LOGGER.exception(msg)
                raise StandardError(msg)
