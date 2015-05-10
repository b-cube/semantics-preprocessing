import luigi
import glob
import os
from tasks.parse_tasks import ParseTask
from tasks.task_helpers import parse_yaml
from tasks.task_helpers import run_init
from optparse import OptionParser


class ParseWorkflow(luigi.Task):
    doc_dir = luigi.Parameter()
    yaml_file = luigi.Parameter()

    start_index = luigi.Parameter(default=0)
    end_index = luigi.Parameter(default=1000)

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
        for f in glob.glob(os.path.join(self.doc_dir, '*.json'))[self.start_index:self.end_index]:
            yield f


def main():
    op = OptionParser()
    op.add_option('--interval', '-i', default=1000)
    op.add_option('--directory', '-d')
    op.add_option('--config', '-c')

    options, arguments = op.parse_args()

    if not options.config:
        op.error('No configuration YAML')
    if not options.directory:
        op.error('No input file directory')

    files = glob.glob(os.path.join(options.directory, '*.json'))
    if not files:
        op.error('Empty input file directory (no JSON)')

    try:
        interval = int(options.interval)
    except:
        op.error('Non-integer interval value')

    for i in xrange(0, len(files), interval):
        w = ParseWorkflow(
            doc_dir=options.directory,
            yaml_file=options.config,
            start_index=i,
            end_index=(i + interval)
        )
        luigi.build([w], local_scheduler=True)

        # w = ParseWorkflow(
        #     doc_dir='testdata/solr_20150320/docs/',
        #     yaml_file='tasks/parse_20150320.yaml',
        #     start_index=i,
        #     end_index=(i + interval)
        # )
        # luigi.build([w], local_scheduler=True)

    # for the response only: python luigi_tasks.py ResponseTask
    #       --input-path 'testdata/docs/response_0a80f182ed59a834572e2c594aacfe29.json'
    #       --output-path 'testdata/luigi/0a80f182ed59a834572e2c594aacfe29_response.json'
    #       --local-scheduler

if __name__ == '__main__':
    main()
