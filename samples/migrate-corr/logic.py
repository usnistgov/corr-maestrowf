"""
Handles the contract between Maestrowf and CoRR

Maestrowf contracts with the following endpoints:

/projects                                    GET
/project/create                              POST
/project/record/create/<project_id>          POST
/project/record/update/<record_id>           POST

and should both accept and return JSON-encoded data when the Accept header is
"application/json".

The required JSON structure can be seen in serialization.json


:Credit<Jessica, Joe, Daniel, Yannick>
"""

from warnings import warn
from urlparse import urlparse, urlunparse
try:
    import httplib2
    import requests
    have_http = True
except ImportError:
    have_http = False

import json

import yaml


API_VERSION = 1

sub_stores = ["http://10.0.1.119/", "http://localhost:5100"]


def domain(url):
    return urlparse(url).netloc


def process_url(url):
    """Strip out username and password if included in URL"""
    username = None
    password = None
    if '@' in url:  # allow encoding username and password in URL - deprecated in RFC 3986, but useful on the command-line
        parts = urlparse(url)
        username = parts.username
        password = parts.password
        hostname = parts.hostname
        if parts.port:
            hostname += ":%s" % parts.port
        url = urlunparse((parts.scheme, hostname, parts.path, parts.params, parts.query, parts.fragment))
    return url, username, password


class HttpCoRRStore:
    """
    Handles storage of simulation/analysis records on the CoRR backend.

    The server should support the following URL structure and HTTP methods:

    This store implements the contract for maestrowf.
    """

    def __init__(self, server_url='', disable_ssl_certificate_validation=True):
        if 'http' in server_url:
            self.server_url = server_url
        else:
            config = {}
            # We will ignore reding this file for now.
            with open(server_url, 'r') as config_file:
                config = json.loads(config_file.read())

            # config = {
            #     "default": {
            #         "api": {
            #             "host": "http://10.0.1.119",
            #             "key": "ab4c3167ee220787d00d91b3976b349184abb08ea91dcc6bebefe62cb05f0a2a",
            #             "path": "/corr/api/v0.1",
            #             "port": 5100
            #         },
            #         "app": "032356f8d58ae905b2128107d84726d7991cc1d27338d129fc55a2ed58177c1a"
            #     }
            # }

            scope = config.get('default', {})
            api = scope.get('api',{})
            host = api.get('host','')
            port = api.get('port', 80)
            key = api.get('key', '')
            path = api.get('path', '')
            token = scope.get('app', '')
            self.server_url = "{0}:{1}{2}/private/{3}/{4}/".format(host, port, path, key, token)
        self.client = httplib2.Http('.cache', disable_ssl_certificate_validation=disable_ssl_certificate_validation)

    def __str__(self):
        return "Interface to the CoRR backend API store at %s using HTTP" % self.server_url

    def __getstate__(self):
        return {
            'server_url': self.server_url
        }

    def __setstate__(self, state):
        self.__init__(state['server_url'])

    def _get(self, url):
        headers = {'Accept': 'application/json'}
        response, content = self.client.request(url, headers=headers)
        return response, content

    def _upload_file(self, record_id, file_path, group):
        url = "%sfile/upload/%s/%s" % (self.server_url, group, record_id)
        files = {'file':open(file_path)}
        response = requests.post(url, files=files, verify=False)
        return response

    def create_project(self, project_name, long_name='', description=''):
        """Create an empty project in the record store."""
        url = "%sproject/create" % (self.server_url)
        content = {'name':project_name, 'goals':long_name, 'description':description}
        headers = {'Content-Type': 'application/json'}
        response, content = self.client.request(url, 'POST', json.dumps(content), headers=headers)
        if response.status != 200:
            print("%d\n%s" % (response.status, content))
            return None
        else:
            project_payload = json.loads(content)
            code = project_payload['code']
            if code != 201:
                raise RecordStoreAccessError("%d\n%s" % (response.status, content))
            else:
                return project_payload

    def get_project(self, project_name):
        project = None
        url = "%sprojects" % (self.server_url)

        response, content = self._get(url)
        if response.status != 200:
            print("Error in accessing %s\n%s: %s" % (url, response.status, content))
            return None
        else:
            projects_payload = json.loads(content)
            code = projects_payload['code']
            if code != 200:
                print("%d\n%s" % (response.status, content))
                return None
            else:
                for p in projects_payload['content']['projects']:
                    if p['name'] == project_name:
                        project = p
                        break
                return project

    def create_record(self, project_name, record):
        """Create an empty record object."""
        record_id = None
        project = None
        url = "%sprojects" % (self.server_url)
        response, content = self._get(url)
        project = None
        if response.status != 200:
            print("Error in accessing %s\n%s: %s" % (url, response.status, content))
            return None
        else:
            project_payload = json.loads(content)
            code = project_payload['code']
            if code != 200:
                print("%d\n%s" % (response.status, content))
                return None
            else:
                for p in project_payload['content']['projects']:
                    if p['name'] == project_name:
                        project = p
                        break
        if project is None:
            project = self.create_project(project_name)

        url = "%sproject/record/create/%s" % (self.server_url, project['id'])
        headers = {'Content-Type': 'application/json'}
        _content = record
        _content['status'] = 'started'
        response, content = self.client.request(url, 'POST', json.dumps(_content),
                                                headers=headers)
        if response.status != 200:
            print("%d\n%s" % (response.status, content))
            return None
        else:
            record_payload = json.loads(content)
            code = record_payload['code']
            if code != 201:
                print("%d\n%s" % (response.status, content))
                return None
            else:
                # Record Meta-Data as JSON.
                return record_payload['content']

    def update_record(self, record, metadata):
        record_id = record['head']['id']
        metadata['project'] = record['head']['project']['id']
        url = "%srecord/update/%s" % (self.server_url, record_id)
        headers = {'Content-Type': 'application/json'}
        response, content = self.client.request(url, 'POST', json.dumps(metadata),
                                                headers=headers)
        if response.status != 200:
            print("%d\n%s" % (response.status, content))
            return None
        else:
            record_payload = json.loads(content)
            code = record_payload['code']
            if code != 201:
                print("%d\n%s" % (response.status, content))
                return None
            else:
                return record_payload['content']

if __name__ == '__main__':
    yaml_content = None
    with open("sample.yml", 'r') as yml_file:
        yaml_content = yaml.load(yml_file.read())
    print(yaml_content)
    # Setup the contract instance.
    corrContract = HttpCoRRStore()

    # Prep project basic data
    project_data = {}
    project_data['name'] = "Test-From-Contract"
    project_data['description'] = "This is a contract for Maestro to CoRR."

    # Create a project
    project_payload = corrContract.create_project(project_name=project_data['name'], long_name='', description=project_data['description'])
    print(json.dumps(project_payload, sort_keys=True, indent=4, separators=(',', ': ')))

    # Get a project and Create if it does not exist.
    project_payload = corrContract.get_project("Test-From-Contract")
    print(json.dumps(project_payload, sort_keys=True, indent=4, separators=(',', ': ')))

    # Create 5 records
    records = []
    for i in range(5):
        record = yaml_content
        records.append(corrContract.create_record(project_name=project_data['name'], record=record))

    print(json.dumps(records, sort_keys=True, indent=4, separators=(',', ': ')))

    # # Update 5 records metadata
    # for i in range(5):
    #     record = records[i]
    #     # schema = {}
    #     # schema['application'] = "string"
    #     # schema['parent'] = "string"
    #     # schema['label'] = "string"
    #     # schema['tags'] = "list of strings"
    #     # schema['system'] = "dict"
    #     # schema['execution'] = "dict"
    #     # schema['inputs'] = "list of dicts"
    #     # schema['outputs'] = "list of dicts"
    #     # schema['dependencies'] = "list of dicts"
    #     # schema['access'] = "private|protected|public"
    #     # schema['status'] = 'starting|started|paused|sleeping|finished|crashed|terminated|resumed|running|unknown'
    #     # schema['resources'] = "list of files meta-data"
    #     # schema['rationels'] = "list of rationels"

    #     _content = {}
    #     #Tofix
    #     _content['execution'] = "../lulesh/lulesh2.0 -s $(SIZE) -i $(ITERATIONS) -p > $(outfile)"
    #     _content['application'] = "Maestrof"
    #     _content['status'] = "finished"
    #     _content['outputs'] = [{"encoding": "utf-8", "path":"lulesh_sample1_20170911/lulesh_sample1.pkl", "mimetype":"bin/pkl", "size":1263}]
    #     _content['inputs'] = [{"encoding": "utf-8", "path":"lulesh_sample1_20170911/lulesh_sample1.yaml", "mimetype":"text/yml", "size":233}]
    #     corrContract.update_record(record, _content)

    # # Upload files to the 5 records metadata
    # for i in range(5):
    #     record = records[i]
    #     path_root = "lulesh_sample1_20170911-152026"
    #     path_out = "%s/lulesh_sample1.pkl"%(path_root)
    #     corrContract._upload_file(record_id=record['head']['id'], file_path=path_out, group="output")
    #     path_in = "%s/lulesh_sample1.yaml"%(path_root)
    #     corrContract._upload_file(record_id=record['head']['id'], file_path=path_in, group="input")
