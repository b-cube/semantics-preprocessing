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

    def test_strip_unicode_replace(self):
        test_string = '''Test the Web Forward\\ufffd\\ufffdParis,\\ufffd\\ufffdBeijing\\ufffd\\ufffdand\\ufffd\\ufffd San Francisco'''
        expected_string = 'Test the Web Forward  Paris,  Beijing  and   San Francisco'

        rr = RawResponse('', test_string, '', **{})
        rr._extract_from_cdata()
        rr._strip_unicode_replace()

        self.assertTrue(rr.content == expected_string)

        test_string = 'Con\\ufffd\\ufffdfu\\ufffd\\ufffdcius Insti\\ufffd\\ufffdtute'
        expected_string = 'Con  fu  cius Insti  tute'

        rr = RawResponse('', test_string, '', **{})
        rr._extract_from_cdata()
        rr._strip_unicode_replace()

        self.assertTrue(rr.content == expected_string)
