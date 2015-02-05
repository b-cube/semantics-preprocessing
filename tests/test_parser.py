import unittest
from parser import Parser
from rdflib import Literal


class TestParser(unittest.TestCase):
    def setUp(self):
        self.parser = Parser()