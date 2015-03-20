import luigi
from lib.rawresponse import RawResponse
from lib.parser import Parser
from lib.identifier import Identify
from lib.process_router import Processor
import json


def read_data(path):
    with open(path, 'r') as f:
        return json.loads(f.read())


def write_data(path, data):
    with open(path, 'w') as f:
        f.write(json.dumps(data, indent=4))


class ResponseTask(luigi.Task):
    input_path = luigi.Parameter()

    def requires(self):
        pass

    def output(self):
        return luigi.LocalTarget(self.input_path + '.cleaned')

    def parameters(self):
        return self.cleaned

    def run(self):
        '''  '''
        data = read_data(self.input_path)
        self.cleaned = self.process_response(data)
        # write_data(self.output_path, cleaned)
        with self.output().open('w') as out_file:
            out_file.write(json.dumps(self.cleaned, indent=4))

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

    def requires(self):
        # return self.upstream_task
        return ResponseTask(self.input_path)

    def output(self):
        return luigi.LocalTarget(self.input_path + '.identified')

    def run(self):
        '''  '''
        f = self.input().open('r')
        data = json.loads(f.read())

        identified = self.process_response(data)

        with self.output().open('w') as out_file:
            out_file.write(json.dumps(identified, indent=4))

    def process_response(self, data):
        content = data['content'].encode('unicode_escape')
        url = data['source_url']
        parser = Parser(content)

        identify = Identify(self.yaml_file, content, url, **{'parser': parser, 'ignore_case': True})
        identify.identify()
        data['identity'] = identify.to_json()
        return data


class ParseTask(luigi.Task):
    yaml_file = luigi.Parameter()
    input_path = luigi.Parameter()

    def requires(self):
        return IdentifyTask(input_path=self.input_path, yaml_file=self.yaml_file)

    def output(self):
        return luigi.LocalTarget(self.input_path + '.parsed')

    def run(self):
        '''  '''
        f = self.input().open('r')
        data = json.loads(f.read())
        parsed = self.process_response(data)
        if parsed:
            with self.output().open('w') as out_file:
                out_file.write(json.dumps(parsed, indent=4))

    def process_response(self, data):
        content = data['content'].encode('unicode_escape')
        url = data['source_url']
        identity = data['identity']

        processor = Processor(identity, content)
        if not processor:
            return {}

        description = processor.reader.parse_service()
        description['solr_identifier'] = data['digest']
        description['source_url'] = url

        # drop the source for a decent non-xml embedded in my json file
        del data['content']

        data["service_description"] = description
        return data
