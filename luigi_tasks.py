import luigi
from lib.rawresponse import RawResponse
from lib.parser import Parser
from lib.identifier import Identify
from lib.preprocessors import *

import json


def read_data(path):
    with open(path, 'r') as f:
        return json.loads(f.read())


def write_data(path, data):
    with open(path, 'w') as f:
        f.write(json.dumps(data, indent=4))


class ResponseTask(luigi.Task):
    input_path = luigi.Parameter()
    output_path = luigi.Parameter()

    def requires(self):
        pass

    def output(self):
        return luigi.LocalTarget(self.output_path)

    def run(self):
        '''  '''
        data = read_data(self.input_path)
        cleaned = self.process_response(data)
        write_data(self.output_path, cleaned)

    def process_response(self, data):
        # do the response processing
        source_url = data['url']
        content = data['raw_content']
        digest = data['digest']

        rr = RawResponse(source_url.upper(), content, digest, **{})
        cleaned_text = rr.clean_raw_content()

        # again sort of ridiculous
        return {
            "digest": digest,
            "source_url": source_url,
            "content": cleaned_text
        }


class IdentifyTask(luigi.Task):
    yaml_file = luigi.Parameter()
    input_path = luigi.Parameter()
    output_path = luigi.Parameter()

    def requires(self):
        return ResponseTask(
            input_path="testdata/docs/response_0a80f182ed59a834572e2c594aacfe29.json",
            output_path="testdata/luigi/0a80f182ed59a834572e2c594aacfe29_cleaned.json"
        )

    def output(self):
        return luigi.LocalTarget(self.output_path)

    def run(self):
        '''  '''
        data = read_data(self.input_path)
        identified = self.process_response(data)
        write_data(self.output_path, identified)

    def process_response(self, data):
        content = data['content']
        url = data['source_url']
        parser = Parser(content)

        identify = Identify(self.yaml_file, content, url, **{'parser': parser, 'ignore_case': True})
        identify.identify()
        return data.update({'identity': identify.to_json()})


class ParseTask(luigi.Task):
    input_path = luigi.Parameter()
    output_path = luigi.Parameter()

    def requires(self):
        return IdentifyTask(
            yaml_file="lib/configs/identifiers.yaml",
            input_path="testdata/luigi/0a80f182ed59a834572e2c594aacfe29_cleaned.json",
            output_path="testdata/luigi/0a80f182ed59a834572e2c594aacfe29_identity.json"
        )

    def output(self):
        return luigi.LocalTarget(self.output_path)

    def run(self):
        '''  '''
        data = read_data(self.input_path)
        parsed = self.process_response(data)
        write_data(self.output_path, parsed)

    def process_response(self, data):
        content = data['content']
        url = data['source_url']
        identity = data['identity']
        protocol = identity['protocol']

        if protocol == 'OpenSearch':
            reader = OpenSearchReader(content)
        elif protocol == 'UNIDATA':
            reader = ThreddsReader(content)
        elif protocol == 'ISO-19115':
            reader = IsoReader(content)
        elif protocol == 'OAI-PMH':
            reader = OaiPmhReader(content)

        description = reader.parse_service()
        description['solr_identifier'] = data['digest']
        description['source_url'] = url

        return data.update({"service_description": description})


if __name__ == '__main__':
    #luigi.run(["--local-scheduler"], main_task_cls=ResponseTask)
    luigi.run()

    # for the response only: python luigi_tasks.py ResponseTask --input-path 'testdata/docs/response_0a80f182ed59a834572e2c594aacfe29.json' --output-path 'testdata/luigi/0a80f182ed59a834572e2c594aacfe29_response.json' --local-scheduler


    # tasks = {}
    # tasks['clean'] = ResponseTask()
    # tasks['identify'] = IdentifyTask(upstream_task=tasks['clean'],
    #                                  yaml_file="lib/configs/identifiers.yaml")
    # tasks['parse'] = ParseTask(upstream_task=tasks['identify'])

    # task_to_run = tasks['clean']

    # luigi.build(task_to_run, local_scheduler=True)
