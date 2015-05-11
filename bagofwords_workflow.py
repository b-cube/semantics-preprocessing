import luigi
import glob
import os
from tasks.text_tasks import BagOfWordsFromParsedTask
from tasks.text_tasks import BagOfWordsFromXML
from tasks.task_helpers import parse_yaml
from tasks.task_helpers import run_init


class BowWorkflow(luigi.Task):
    doc_dir = luigi.Parameter()
    yaml_file = luigi.Parameter()

    start_index = luigi.Parameter(default=0)
    end_index = luigi.Parameter(default=1000)

    def requires(self):
        return [
            BagOfWordsFromParsedTask(
                input_file=f,
                yaml_file=self.yaml_file
            ) for f in self._iterator()
        ]

    def output(self):
        return luigi.LocalTarget('log.txt')

    def run(self):
        print 'running'

    def _iterator(self):
        for f in glob.glob(os.path.join(self.doc_dir, '*.json'))[self.start_index:self.end_index]:
            yield f

    def _configure(self):
        config = parse_yaml(self.yaml_file)
        run_init(config)


class BowFromXmlWorkflow(luigi.Task):
    doc_dir = luigi.Parameter()
    yaml_file = luigi.Parameter()

    start_index = luigi.Parameter(default=0)
    end_index = luigi.Parameter(default=1000)

    def requires(self):
        return [
            BagOfWordsFromXML(
                input_file=f,
                yaml_file=self.yaml_file
            ) for f in self._iterator()
        ]

    def output(self):
        return luigi.LocalTarget('log.txt')

    def run(self):
        print 'running'

    def _iterator(self):
        for f in glob.glob(os.path.join(self.doc_dir, '*.json'))[self.start_index:self.end_index]:
            yield f

    def _configure(self):
        config = parse_yaml(self.yaml_file)
        run_init(config)
