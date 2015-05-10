import luigi
from tasks.eda_tasks import IdentityEDATask
from tasks.task_helpers import parse_yaml
from tasks.task_helpers import run_init


class IdentifyEDAWorkflow(luigi.Task):
    '''
    compile the identify json into a csv and
    do some very basic pandas aggregation to
    another csv
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
    w = IdentifyEDAWorkflow(yaml_file='tasks/identity_eda_20150414_firstharvest.yaml')
    luigi.build([w], local_scheduler=True)
