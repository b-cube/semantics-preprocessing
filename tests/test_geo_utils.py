# -*- coding: utf-8 -*-

import unittest
from lib.geo_utils import identify_epsg, define_spref, reproject, bbox_to_geom, gml_to_geom, to_wkt
from osgeo import ogr


class TestGeoUtils(unittest.TestCase):
    def setUp(self):
        self.bbox = [-79.3, 30.0, 22.4, 43.6]
        self.gml = '''<gml:Polygon gml:id="US3PR10M_P1" srsName="urn:ogc:def:crs:EPSG::4326">
                        <gml:exterior>
                            <gml:LinearRing>
                                <gml:pos>18.3798 -64.90292</gml:pos>
                                <gml:pos>18.3755 -64.90292</gml:pos>
                                <gml:pos>18.3755 -64.62383</gml:pos>
                                <gml:pos>18.1666 -64.62383</gml:pos>
                                <gml:pos>18.1666 -64.41686</gml:pos>
                                <gml:pos>17.6722 -64.41711</gml:pos>
                                <gml:pos>17.6289 -64.41711</gml:pos>
                                <gml:pos>17.5813 -64.41667</gml:pos>
                                <gml:pos>17.1707 -64.41667</gml:pos>
                                <gml:pos>17.1707 -68.00001</gml:pos>
                                <gml:pos>19.0063 -68.00001</gml:pos>
                                <gml:pos>19.0063 -64.90292</gml:pos>
                                <gml:pos>18.3798 -64.90292</gml:pos>
                            </gml:LinearRing>
                        </gml:exterior>
                    </gml:Polygon>'''

    def test_identify_epsg(self):
        self.assertTrue('EPSG:4326' == identify_epsg('EPSG:4326'))
        self.assertTrue('EPSG:4326' == identify_epsg('urn:ogc:def:crs:OGC:1.3:CRS84'))
        self.assertTrue('EPSG:4326' != identify_epsg('CRS:83'))
        self.assertTrue('EPSG:4326' == identify_epsg('CRS:84'))
        self.assertTrue('EPSG:4326' == identify_epsg('urn:ogc:def:crs:EPSG::4326'))

    def test_bbox_to_geom(self):
        geom = bbox_to_geom(self.bbox)

        self.assertTrue(geom is not None)
        self.assertTrue(isinstance(geom, ogr.Geometry))

    def test_gml_to_geom(self):
        geom = gml_to_geom(self.gml)
        self.assertTrue(geom is not None)

    def test_geom_to_wkt(self):
        test_wkt = 'POLYGON ((-79.3 30.0,-79.3 43.6,22.4 43.6,22.4 30.0,-79.3 30.0))'
        geom = bbox_to_geom(self.bbox)
        wkt = to_wkt(geom)
        self.assertTrue(wkt == test_wkt)

    def test_reproject(self):
        pass
