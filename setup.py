from setuptools import setup, find_packages
import semproc
from setuptools.command.test import test as TestCommand
import sys


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

readme = open('README.md').read()
reqs = [line.strip() for line in open('basic_requirements.txt')]

setup(name='Semantics-Preprocessing',
      version=semproc.__version__,
      description='Web Service Parsers for B-Cube pipelines',
      long_description=readme,
      license='MIT',
      keywords='opensearch oai-pmh rdf thredds opendap ogc iso 19115 fgdc dif ows wfs wms sos csw wcs capabilities metadata wmts',
      author='Soren Scott',
      author_email='sorenscott@gmail.com',
      maintainer='Soren Scott',
      maintainer_email='sorenscott@gmail.com',
      url='http://github.io/bcube/semantics-preprocessors',
      install_requires=reqs,
      cmdclass={'test': PyTest},
      packages=find_packages(exclude=["local", "response_examples", "tests"])
)
