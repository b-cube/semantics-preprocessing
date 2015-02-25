import unittest
from lib.preprocessors.ows_preprocessors import OwsWmsPreprocessor
from lib.preprocessors.ows_preprocessors import OwsWcsPreprocessor
from lib.preprocessors.ows_preprocessors import OwsWfsPreprocessor


class TestOwsWmsPreprocessor(unittest.TestCase):
    def setUp(self):
        with open('tests/test_data/wms_v1.1.1.xml', 'r') as f:
            text = f.read()
        self.reader = OwsWmsPreprocessor(text, '1.1.1')

    def test_return_descriptors(self):
        descriptors = self.reader.return_service_descriptors()

        self.assertTrue('Tropical Rainfall Measuring' in descriptors['title'])
        self.assertFalse(descriptors['version'] == "1.0.2")


class TestOwsWcsPreprocessor(unittest.TestCase):
    def setUp(self):
        with open('tests/test_data/wcs_v1_0_0.xml', 'r') as f:
            text = f.read()
        self.reader = OwsWcsPreprocessor(text, '1.0.0')

    def test_return_descriptors(self):
        # self.assertTrue(self.reader.reader)

        descriptors = self.reader.return_service_descriptors()

        self.assertTrue('GMU LAITS Web Coverage Server' in descriptors['title'])
        self.assertFalse(descriptors['version'] == "1.0.2")


class TestOwsWfsPreprocessor100(unittest.TestCase):
    def setUp(self):
        # tests/test_data/wfs_v1_0_0.xml is the original invalid wfs
        with open('tests/test_data/wfs_v1_0_0_valid.xml', 'r') as f:
            text = f.read()
        self.reader = OwsWfsPreprocessor(text, '1.0.0')

    def test_return_descriptors(self):
        # self.assertTrue(self.reader.reader)

        descriptors = self.reader.return_service_descriptors()

        self.assertTrue('GMU LAITS Web Coverage Server' in descriptors['title'])
        self.assertFalse(descriptors['version'] == "1.0.2")


class TestOwsWfsPreprocessor110(unittest.TestCase):
    def setUp(self):
        with open('tests/test_data/wfs_v1_1_0.xml', 'r') as f:
            text = f.read()
        self.reader = OwsWfsPreprocessor(text, '1.1.0')

    def test_return_descriptors(self):
        # self.assertTrue(self.reader.reader)

        descriptors = self.reader.return_service_descriptors()

        self.assertTrue('GMU LAITS Web Coverage Server' in descriptors['title'])
        self.assertFalse(descriptors['version'] == "1.0.2")
