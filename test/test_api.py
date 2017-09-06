import json
from urllib2 import HTTPError
import unittest

from projestions_api import get_projestions


class ApiTest(unittest.TestCase):

    def test_get_projestions_empty(self):
        """Test get_projestions with emtpy input"""
        with self.assertRaises(HTTPError):
            get_projestions(None)

    def test_get_projestions_feature(self):
        """Test get_projestions with feature"""
        geojson = {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Point",
                "coordinates": [
                    -73.9324951171875,
                    40.74725696280421
                ]
            }
        }
        get_projestions(json.dumps(geojson))

    def test_get_projestions_feature_collection(self):
        """Test get_projestions with feature collection"""
        geojson = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        -73.9324951171875,
                        40.74725696280421
                    ]
                }
            }]
        }
        get_projestions(json.dumps(geojson))


if __name__ == '__main__':
    unittest.main()
