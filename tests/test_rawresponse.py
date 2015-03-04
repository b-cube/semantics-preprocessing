import unittest
from lib.rawresponse import RawResponse


class TestRawResponse(unittest.TestCase):
    def setUp(self):
        pass

    def test_strip_cdata(self):
        test_string = u'<![CDATA[<xml><node>Hi</node></xml>]]>'
        expected_string = '<xml><node>Hi</node></xml>'

        rr = RawResponse('', test_string, '', **{})

        rr._extract_from_cdata()

        returned_string = rr.content

        self.assertTrue(expected_string == returned_string)

    def test_strip_invalid_start(self):
        test_string = '<![CDATA[\ufffd\ufffd\ufffd<xml><node>Hi</node></xml>]]>'
        expected_string = '<xml><node>Hi</node></xml>'

        rr = RawResponse('', test_string, '', **{})

        rr._extract_from_cdata()
        rr._strip_invalid_start()

        returned_string = rr.content

        self.assertTrue(expected_string == returned_string)
