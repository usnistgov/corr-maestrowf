import unittest
import json

from maestrowf.interfaces.archive.corrarchiveadapter import CorrHttpAdapter
from maestrowf.interfaces.archive import utils

class TestCorrHttpAdapter(unittest.TestCase):

    def setUp(self):
        config_path = '../generic-config.json'
        self.corr_adap = CorrHttpAdapter(config_path=config_path)
        self.maestro_spec_path = utils.get_file_path('lulesh_sample1.yaml')
        self.maestro_spec_path_not_corr = utils.get_file_path('lulesh_sample2.yaml')

    def test_create_CorHttpAdapater(self):
        config_path = '../generic-config.json'
        my_corr_adap = CorrHttpAdapter(config_path=config_path)
        host = "http://10.0.1.119"
        port = "5100"
        key = "7b37a3ff1184cb4f5ae04b3b175cfb6a63d2c6843ed051ccebfa87d8b35df4f4"
        path = "/corr/api/v0.1"
        token =  "032356f8d58ae905b2128107d84726d7991cc1d27338d129fc55a2ed58177c1a"
        self.assertTrue(my_corr_adap.server_url, '{0}:{1}{2}/private/{3}/{4}/'\
            ''.format(host, port, path, key, token))

    #@unittest.skip("Skip create project.")
    def test_create_project(self):
        response, content = self.corr_adap.create_project(self.maestro_spec_path)
        self.assertEqual(response.status, 200)

    #@unittest.skip("Skip update project.")
    def test_update_project_good(self):
        response, content = self.corr_adap.update_project(self.maestro_spec_path)
        self.assertEqual(response.status, 200)

    #@unittest.skip("Skip update project.")
    def test_update_project_bad(self):
        with self.assertRaises(StandardError) as context:
            self.corr_adap.update_project(self.maestro_spec_path_not_corr)

    def test_has_project(self):
        project_name = 'lulesh_sample1'
        self.assertTrue(self.corr_adap.has_project(project_name=project_name))

    #@unittest.skip("Skip create record.")
    def test_insert_record(self):
        project_name = 'lulesh_sample1'
        corr_spec_path = 'corr-out.yaml'
        response, content = self.corr_adap.create_record(
                                                project_name=project_name,
                                                corr_spec_path=corr_spec_path)
        self.record_id = json.loads(content)['content']['head']['id']
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(content)['code'], 201)

    #@unittest.skip("Skip update record.")
    def test_update_record(self):
        project_name = 'lulesh_sample1'
        corr_spec_path = 'corr-out.yaml'
        corr_spec_path_update = 'corr-out_update.yaml'
        response, content = self.corr_adap.create_record(
                                                project_name=project_name,
                                                corr_spec_path=corr_spec_path)
        record_id = json.loads(content)['content']['head']['id']
        response, content = self.corr_adap.update_record(
                                                project_name=project_name,
                                                record_id=record_id,
                                                corr_spec_path=corr_spec_path_update)
        print content
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(content)['code'], 201)
