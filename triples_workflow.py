import luigi
import glob
import os
from tasks.text_tasks import TextPreprocessingTask
from tasks.task_helpers import parse_yaml
from tasks.task_helpers import run_init


class TripleWorkflow(luigi.Task):
    '''
    get, clean, identify, parse, detect language,
    normalize keywords, generate triples, push to
    triplestore
    '''
    yaml_file = luigi.Parameter()
    doc_dir = luigi.Parameter()

    start_index = luigi.Parameter(default=0)
    end_index = luigi.Parameter(default=1000)

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
        for f in glob.glob(os.path.join(self.doc_dir, '*.json'))[self.start_index:self.end_index]:
            yield f


if __name__ == '__main__':
    '''
    currently starts at the text preprocessing task
    '''
    # TODO: revise to start, tail-first, at the generate triples/post triples task
    interval = 2000
    for i in xrange(0, 26000, interval):
        w = TripleWorkflow(
            doc_dir='testdata/docs/',
            yaml_file='tasks/test_config.yaml',
            start_index=i,
            end_index=(i + interval)
        )
        luigi.build([w], local_scheduler=True)
