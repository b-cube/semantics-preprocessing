import luigi
import glob
import os
from tasks.parse_tasks import ParseTask, IdentifyTask
from tasks.text_tasks import TextPreprocessingTask
from tasks.eda_tasks import IdentityEDATask
from tasks.task_helpers import parse_yaml, extract_task_config
from tasks.task_helpers import run_init


class ParseWorkflow(luigi.Task):
    doc_dir = luigi.Parameter()
    yaml_file = luigi.Parameter()

    def requires(self):
        return [ParseTask(input_file=f, yaml_file=self.yaml_file) for f in self._iterator()]

    def output(self):
        return luigi.LocalTarget('log.txt')

    def run(self):
        self._configure()
        print 'running'

    def _configure(self):
        config = parse_yaml(self.yaml_file)
        run_init(config)

    def _iterator(self):
        for f in glob.glob(os.path.join(self.doc_dir, '*.json'))[0:2]:
            yield f


class BowWorkflow(luigi.Task):
    doc_dir = luigi.Parameter()
    yaml_file = luigi.Parameter()

    def requires(self):
        return [ParseTask(input_path=f, yaml_file=self.yaml_file) for f in self._iterator()]

    def output(self):
        return luigi.LocalTarget('log.txt')

    def run(self):
        print 'running'

    def _iterator(self):
        for f in glob.glob(os.path.join(self.doc_dir, '*.json'))[0:10]:
            yield f


class TripleWorkflow(luigi.Task):
    '''
    get, clean, identify, parse, detect language,
    normalize keywords, generate triples, push to
    triplestore
    '''
    yaml_file = luigi.Parameter()
    doc_dir = luigi.Parameter()

    def requires(self):
        return [
            TextPreprocessingTask(
                input_file=f, yaml_file=self.yaml_file
            ) for f in self._iterator()
        ]

    def output(self):
        return luigi.LocalTarget('log.txt')

    def run(self):
        self._configure()
        print 'running'

    def _configure(self):
        config = parse_yaml(self.yaml_file)
        run_init(config)

    def _iterator(self):
        for f in glob.glob(os.path.join(self.doc_dir, '*.json'))[0:10]:
            yield f


class IdentifyWorkflow(luigi.Task):
    doc_dir = luigi.Parameter()
    yaml_file = luigi.Parameter()

    def requires(self):
        return [IdentifyTask(input_file=f, yaml_file=self.yaml_file) for f in self._iterator()]

    def output(self):
        return luigi.LocalTarget('log.txt')

    def run(self):
        self._configure()
        print 'running'

    def _configure(self):
        config = parse_yaml(self.yaml_file)
        run_init(config)

    def _iterator(self):
        for f in glob.glob(os.path.join(self.doc_dir, '*.json'))[2000:5000]:
            yield f


class IdentifyEDAWorkflow(luigi.Task):
    '''

    '''
    yaml_file = luigi.Parameter()

    def requires(self):
        return IdentityEDATask(yaml_file=self.yaml_file)

    def output(self):
        return luigi.LocalTarget('log.txt')

    def run(self):
        self._configure()
        print 'running'

    def _configure(self):
        config = parse_yaml(self.yaml_file)
        run_init(config)


if __name__ == '__main__':
    # yaml_file = the configuration yaml for all tasks

    # this is quite unfortunate
    # w = ParseWorkflow(doc_dir='testdata/docs/', yaml_file='tasks/test_config.yaml')
    # w = TripleWorkflow(doc_dir='testdata/docs/', yaml_file='tasks/test_config.yaml')
    # w = IdentifyEDAWorkflow(yaml_file='tasks/identity_eda.yaml')
    w = IdentifyWorkflow(doc_dir='testdata/solr_20150320/docs/', yaml_file='tasks/identity_20150320.yaml')

    luigi.build([w], local_scheduler=True)

    # for the response only: python luigi_tasks.py ResponseTask
    #       --input-path 'testdata/docs/response_0a80f182ed59a834572e2c594aacfe29.json'
    #       --output-path 'testdata/luigi/0a80f182ed59a834572e2c594aacfe29_response.json'
    #       --local-scheduler
