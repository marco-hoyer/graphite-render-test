'''
Created on 29.10.2013

@author: mhoyer
'''
import unittest
import graphite_render_test


class graphite_render_test_test(unittest.TestCase):


    def test_build_graphite_render_url(self):
        self.assertEqual(graphite_render_test.build_graphite_render_url("grphost", "dev.devloadtest902.yum2.rta7", "json", "&from=-5min", False, True),"http://grphost/render/?target=dev.devloadtest902.yum2.rta7&format=json&&from=-5min&local=0&cache=1")

    def test_count_nones(self):
        self.assertEqual(graphite_render_test.count_nones([[49.0, 1383046080], [38.0, 1383046140], [72.0, 1383046200], [54.0, 1383046260], [None, 1383046320]]), 1)
        self.assertEqual(graphite_render_test.count_nones([[49.0, 1383046080]]), 0)
        self.assertEqual(graphite_render_test.count_nones([[None, 1383046080]]), 1)
        self.assertEqual(graphite_render_test.count_nones([]), 0)
        self.assertEqual(graphite_render_test.count_nones(None), 0)
        
    def test_get_graphite_datapoints(self):
        response = '[{"target": "test.testmetric", "datapoints": [[null, 1383049080], [null, 1383049140], [null, 1383049200], [null, 1383049260], [null, 1383049320]]}]'
        self.assertEqual(graphite_render_test.get_graphite_datapoints(response), [[None, 1383049080], [None, 1383049140], [None, 1383049200], [None, 1383049260], [None, 1383049320]])
        response = '[{"target": "test.testmetric", "datapoints": [[1.0, 1383049320]]}]'
        self.assertEqual(graphite_render_test.get_graphite_datapoints(response), [[1.0, 1383049320]])
        response = '[]'
        self.assertEqual(graphite_render_test.get_graphite_datapoints(response), [])
        response = '[{"target": "test.testmetric", "datapoint": [[1.0, 1383049320]]}]'
        self.assertEqual(graphite_render_test.get_graphite_datapoints(response), [])
        response = '[{"target": "test.testmetric", "datapoint" abcdefg [[1.0, 1383049320]]}]'
        self.assertEqual(graphite_render_test.get_graphite_datapoints(response), [])
if __name__ == "__main__":
    unittest.main()