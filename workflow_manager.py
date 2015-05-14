import luigi
import glob
import os
import sys
from optparse import OptionParser
from parse_workflow import ParseWorkflow
from identify_workflow import IdentifyWorkflow
from bagofwords_workflow import BowWorkflow, BowFromXmlWorkflow
from triple_workflow import TripleWorkflow
from extract_identifier_workflow import ExtractIdentifierWorkflow


def main():
    op = OptionParser()
    op.add_option('--interval', '-i', default=1000)
    op.add_option('--directory', '-d')
    op.add_option('--config', '-c')
    op.add_option('--start', '-s')
    op.add_option('--end', '-e')
    op.add_option('--workflow', '-w')

    options, arguments = op.parse_args()

    if not options.config:
        op.error('No configuration YAML')
    if not options.directory:
        op.error('No input file directory')

    if not options.workflow:
        op.error('No workflow specified')

    files = glob.glob(os.path.join(options.directory, '*.json'))
    if not files:
        op.error('Empty input file directory (no JSON)')

    try:
        interval = int(options.interval)
    except:
        op.error('Non-integer interval value')

    start_index = int(arguments.start) if 'start' in arguments else 0
    end_index = int(arguments.end) if 'end' in arguments else len(files)

    # this only works for the workflows imported above (and they
    # need to be imported, obv). things like the eda, which aren't
    # working on a single file dependency tree, need something else
    try:
        workflow_class = getattr(sys.modules[__name__], options.workflow)
    except AttributeError:
        op.error('Unable to load workflow for {0}'.format(options.workflow))

    for i in xrange(start_index, end_index, interval):
        w = workflow_class(
            doc_dir=options.directory,
            yaml_file=options.config,
            start_index=i,
            end_index=(i + interval)
        )
        luigi.build([w], local_scheduler=True)

if __name__ == '__main__':
    '''
    a little cli for running the workflows and
    to manage the standardization across those for
    bulk processing from files
    '''
    main()
