import luigi
import json
from task_helpers import parse_yaml, extract_task_config, load_yamls
from task_helpers import generate_output_filename
from datetime import datetime
import glob
import os
import pandas as pd


class IdentityCollectTask(luigi.Task):
    '''
    from some set of identify task responses, pull
    the json info into a csv file tagged by day
    '''
    yaml_file = luigi.Parameter()

    output_path = ''
    input_path = ''
    delimiter = ','

    def requires(self):
        return []

    def output(self):
        return luigi.LocalTarget(
            generate_output_filename(
                'identity.csv',
                self.output_path,
                datetime.now().strftime('%Y%m%d')
            )
        )

    def run(self):
        '''  '''
        self._configure()

        for response in self.process_response():
            with self.output().open('a') as out_file:
                out_file.write(self.delimiter.join(response) + '\n')

    def _configure(self):
        config = parse_yaml(self.yaml_file)
        config = extract_task_config(config, 'IdentityCollect')
        self.output_path = config.get('output_directory', '')
        self.input_path = config.get('input_directory', '')
        self.delimiter = config.get('delimiter', ',')

    def process_response(self):
        # do the response processing
        if not self.input_path:
            return
        for f in glob.glob(os.path.join(self.input_path, '*.json')):
            with open(f, 'r') as g:
                data = json.loads(g.read())

            identity = data.get('identity', {})
            source_url = data.get('source_url', '')
            digest = data.get('digest', '')

            protocol = identity.get('protocol', '')
            subtype = identity.get('subtype', '')
            service = identity.get('service', '')
            version = identity.get('version', '')
            has_dataset = identity.get('has_dataset', '')
            has_metadata = identity.get('has_metadata', '')

            # return new line: digest, url, protocol, type, service,
            #                  version, has dataset, has metadata
            yield [
                digest,
                source_url,
                protocol,
                subtype,
                service,
                version,
                str(has_dataset),
                str(has_metadata)
            ]


class IdentityEDATask(luigi.Task):
    yaml_file = luigi.Parameter()

    output_path = ''
    delimiter = ','
    aggregation_terms = []

    def requires(self):
        return IdentityCollectTask(yaml_file=self.yaml_file)

    def output(self):
        return luigi.LocalTarget(
            generate_output_filename(
                self.input().path,
                self.output_path,
                'eda'
            )
        )

    def run(self):
        '''  '''
        self._configure()

        df = pd.DataFrame.from_csv(self.input().path, sep=self.delimiter)
        counts = self.process_response(df)
        counts.to_csv(self.output().path)

    def _configure(self):
        config = parse_yaml(self.yaml_file)
        config = extract_task_config(config, 'IdentityEDA')
        self.output_path = config.get('output_directory', '')
        self.delimiter = config.get('delimiter', ',')

        # if the identifier_pattern: get all matches
        identifier_pattern = config.get('identifier_pattern', '')
        if identifier_pattern:
            identifiers = glob.glob(identifier_pattern)

        # if identifiers (list), use only the list values
        identifiers = config.get('identifiers', identifiers)

        # and then use our little yaml loader
        identifier_yaml = load_yamls(identifiers)

        self.aggregation_terms = [y['name'] for y in identifier_yaml]

    def process_response(self, dataframe):
        # do the response processing

        # replace NaN with Unidentified
        df = dataframe.fillna('Unidentified')

        # extract the subset based on the aggregation terms
        if self.aggregation_terms:
            df = df.query('protocol in [%s]' % ','.join(self.aggregation_terms))

        # group and count
        df = df.groupby('protocol')
        counts = df.count('url')

        # return new dataframe
        return counts.to_frame(name="count")
