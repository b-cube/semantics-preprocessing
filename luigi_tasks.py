import luigi
from lib.rawresponse import RawResponse
from lib.parser import Parser
from lib.identifier import Identify
from lib.preprocessors.opensearch_preprocessors import OpenSearchReader
from lib.preprocessors.iso_preprocessors import IsoReader
from lib.preprocessors.oaipmh_preprocessors import OaiPmhReader
from lib.preprocessors.thredds_preprocessors import ThreddsReader

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
        # write_data(self.output_path, cleaned)
        with self.output().open('w') as out_file:
            out_file.write(json.dumps(cleaned, indent=4))

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
    # input_path = luigi.Parameter()
    output_path = luigi.Parameter()
    upstream_task = luigi.Parameter()

    def requires(self):
        return self.upstream_task

    def output(self):
        # print '##########FINISHED IDENTIFY########'
        return luigi.LocalTarget(self.output_path)

    def run(self):
        '''  '''
        # print '##########IDENTIFY########'
        # data = read_data(self.input_path)
        f = self.input().open('r')
        data = json.loads(f.read())

        # if not data:
        #     data = read_data(self.input_path)

        # print '**************!!!!!!!!!!!!!!!!!!!!', self.yaml_file

        identified = self.process_response(data)
        # write_data(self.output_path, identified)

        # print '**************!!!!!!!!!!!!!!!!!!!!'

        with self.output().open('w') as out_file:
            out_file.write(json.dumps(identified, indent=4))

    def process_response(self, data):
        content = data['content'].encode('unicode_escape')
        url = data['source_url']
        parser = Parser(content)

        identify = Identify(self.yaml_file, content, url, **{'parser': parser, 'ignore_case': True})

        # print 'YAML:', identify.yaml
        identify.identify()

        # print identify.to_json()

        data['identity'] = identify.to_json()

        return data


class ParseTask(luigi.Task):
    # input_path = luigi.Parameter()
    output_path = luigi.Parameter()
    upstream_task = luigi.Parameter()

    def requires(self):
        return self.upstream_task

    def output(self):
        return luigi.LocalTarget(self.output_path)

    def run(self):
        '''  '''
        # data = read_data(self.input_path)
        f = self.input().open('r')
        data = json.loads(f.read())

        # print '**************!!!!!!!!!!!!!!!!!!!!', f.read()

        # if not data:
        #     data = read_data(self.input().path)

        # print '**************!!!!!!!!!!!!!!!!!!!!', len(data.keys())

        parsed = self.process_response(data)
        # write_data(self.output_path, parsed)
        with self.output().open('w') as out_file:
            out_file.write(json.dumps(parsed, indent=4))

    def process_response(self, data):
        content = data['content'].encode('unicode_escape')
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

        # print 'DESCRIPTION: ', len(description.keys())

        data["service_description"] = description
        return data


if __name__ == '__main__':
    # luigi.run(["--local-scheduler"], main_task_cls=ResponseTask)
    # luigi.run()

    tasks = {}
    rt = ResponseTask(
        input_path='testdata/docs/response_0a80f182ed59a834572e2c594aacfe29.json',
        output_path='testdata/luigi/0a80f182ed59a834572e2c594aacfe29_cleaned.json'
    )
    it = IdentifyTask(
        upstream_task=rt,
        # input_path='testdata/luigi/0a80f182ed59a834572e2c594aacfe29_cleaned.json',
        output_path='testdata/luigi/0a80f182ed59a834572e2c594aacfe29_identify.json',
        yaml_file='lib/configs/identifiers.yaml'
    )
    pt = ParseTask(
        upstream_task=it,
        # input_path='testdata/luigi/0a80f182ed59a834572e2c594aacfe29_identify.json',
        output_path='testdata/luigi/0a80f182ed59a834572e2c594aacfe29_parse.json'
    )

    luigi.build([pt], local_scheduler=True)

    # for the response only: python luigi_tasks.py ResponseTask --input-path 'testdata/docs/response_0a80f182ed59a834572e2c594aacfe29.json' --output-path 'testdata/luigi/0a80f182ed59a834572e2c594aacfe29_response.json' --local-scheduler

