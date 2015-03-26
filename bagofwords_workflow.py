import luigi
import glob
import os
import argparse
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--bow_type', required=True)
    parser.add_argument('-i', '--interval', required=True)
    parser.add_argument('-s', '--start_index', required=True)
    parser.add_argument('-e', '--end_index', required=True)
    args = parser.parse_args()

    bow_option = args.bow_type
    interval = int(args.interval) if 'interval' in args else 1000
    start_index = int(args.start_index) if 'start_index' in args else 0
    end_index = int(args.end_index) if 'end_index' in args else 2600

    print bow_option

    for i in xrange(start_index, end_index, interval):
        if bow_option in ['BagOfWordsFromXML']:
            # this is silly, luigi
            w = BowFromXmlWorkflow(
                doc_dir='testdata/solr_20150320/clean_20150325',
                yaml_file='tasks/bagofwords_from_xml.yaml',
                start_index=i,
                end_index=(i + interval)
            )
        else:
            w = BowWorkflow(
                doc_dir='testdata/solr_20150320/docs/',
                yaml_file='tasks/bagofwords_20150320.yaml',
                start_index=i,
                end_index=(i + interval)
            )
        luigi.build([w], local_scheduler=True)
