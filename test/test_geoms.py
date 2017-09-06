import json
import sys
from urllib2 import HTTPError
import unittest
from qgis.core import QgsMapLayerRegistry

import projestions_geoms
import settings
from utilities import get_qgis_app, load_data


QGIS_APP = get_qgis_app()

# Initialize Processing for layer_geom test
sys.path.append('/usr/share/qgis/python/plugins')

from processing.core.Processing import Processing
Processing.initialize()


class GeomsTest(unittest.TestCase):

    def assert_valid_extent(self, geojson):
        """Assert given geojson object is a valid extent.

        Should:
         * Not be empty
         * Be a polygon
         * Have coordinates in range of latitude and longitude
         * Have non-zero coordinates (since we're not testing with data around
           Null Island)
        """
        self.assertNotEqual(geojson, '')

        geojson = json.loads(geojson)
        self.assertEqual(geojson['type'], 'Polygon')
        self.assertTrue(geojson['coordinates'][0][0][0] <= 180)
        self.assertTrue(geojson['coordinates'][0][0][0] >= -180)
        self.assertNotEqual(geojson['coordinates'][0][0][0], 0)

    def test_get_layer_extent(self):
        """Test layer_extent"""
        layer = load_data('point-nyc.shp')
        geojson = projestions_geoms.layer_extent(layer)
        self.assert_valid_extent(geojson)

    def test_get_layer_geom(self):
        """Test layer_geom"""
        layer = load_data('point-nyc.shp')
        geojson = projestions_geoms.layer_geom(layer)
        self.assertNotEqual(geojson, '')

        geojson = json.loads(geojson)
        self.assertEqual(geojson['type'], 'FeatureCollection')

    def test_get_layer_geom_large(self):
        """Test layer_geom with many features"""
        layer = load_data('many-points-nyc.shp')
        geojson = projestions_geoms.layer_geom(layer)
        self.assertNotEqual(geojson, '')
        geojson = json.loads(geojson)
        self.assertEqual(geojson['type'], 'FeatureCollection')
        self.assertLessEqual(len(geojson['features']),
                             settings.PROJESTIONS_MAX_FEATURES)

    def test_project_extent(self):
        """Test project_extent"""
        layer = load_data('point-nyc.shp')

        QgsMapLayerRegistry.instance().addMapLayer(layer)
        geojson = projestions_geoms.project_extent()
        self.assert_valid_extent(geojson)

    def test_map_canvas_extent(self):
        """Test map_canvas_extent"""
        layer = load_data('point-nyc.shp')
        QgsMapLayerRegistry.instance().addMapLayer(layer)

        iface = QGIS_APP[2]
        mapCanvas = iface.mapCanvas()
        mapCanvas.zoomToFullExtent()
        geojson = projestions_geoms.map_canvas_extent(mapCanvas)
        self.assert_valid_extent(geojson)


if __name__ == '__main__':
    unittest.main()
