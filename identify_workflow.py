import luigi
import glob
import os
from tasks.parse_tasks import IdentifyTask
from tasks.task_helpers import parse_yaml
from tasks.task_helpers import run_init


class IdentifyWorkflow(luigi.Task):
    doc_dir = luigi.Parameter()
    yaml_file = luigi.Parameter()

    start_index = luigi.Parameter(default=0)
    end_index = luigi.Parameter(default=1000)

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
        for f in glob.glob(os.path.join(self.doc_dir, '*.json'))[self.start_index:self.end_index]:
            yield f


if __name__ == '__main__':
    interval = 1000
    for i in xrange(0, 26000, interval):
        w = IdentifyWorkflow(
            doc_dir='testdata/docs/',
            yaml_file='tasks/identity_20150414_firstharvest.yaml',
            start_index=i,
            end_index=(i + interval)
        )
        luigi.build([w], local_scheduler=True)
