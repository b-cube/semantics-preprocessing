import luigi
from lib.rawresponse import RawResponse
from lib.parser import Parser
from lib.identifier import Identify
from lib.process_router import Processor
import json
from task_helpers import parse_yaml, extract_task_config
from task_helpers import read_data, generate_output_filename
import subprocess


class ResponseTask(luigi.Task):
    yaml_file = luigi.Parameter()
    input_file = luigi.Parameter()

    output_path = ''

    def requires(self):
        return []

    def output(self):
        return luigi.LocalTarget(
            generate_output_filename(
                self.input_file,
                self.output_path,
                'cleaned'
            )
        )

    def run(self):
        '''  '''
        self._configure()

        data = read_data(self.input_file)
        self.cleaned = self.process_response(data)
        with self.output().open('w') as out_file:
            out_file.write(json.dumps(self.cleaned, indent=4))

    def _configure(self):
        config = parse_yaml(self.yaml_file)
        config = extract_task_config(config, 'Clean')
        self.output_path = config.get('output_directory', '')

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
    input_file = luigi.Parameter()

    output_path = ''
    identifiers = []

    def requires(self):
        return ResponseTask(input_file=self.input_file, yaml_file=self.yaml_file)

    def output(self):
        return luigi.LocalTarget(
            generate_output_filename(
                self.input_file,
                self.output_path,
                'identified'
            )
        )

    def run(self):
        '''  '''
        self._configure()

        f = self.input().open('r')
        data = json.loads(f.read())

        identified = self.process_response(data)

        with self.output().open('w') as out_file:
            out_file.write(json.dumps(identified, indent=4))

    def _configure(self):
        config = parse_yaml(self.yaml_file)
        config = extract_task_config(config, 'Identify')
        self.output_path = config.get('output_directory', '')
        self.identifiers = config.get('identifiers', [])

    def process_response(self, data):
        content = data['content'].encode('unicode_escape')
        url = data['source_url']
        parser = Parser(content)

        identify = Identify(
            self.identifiers,
            content,
            url,
            **{'parser': parser, 'ignore_case': True}
        )
        identify.identify()
        data['identity'] = identify.to_json()
        return data


class ParseTask(luigi.Task):
    yaml_file = luigi.Parameter()
    input_file = luigi.Parameter()

    output_path = ''
    params = {}

    def requires(self):
        return IdentifyTask(input_file=self.input_file, yaml_file=self.yaml_file)

    def output(self):
        return luigi.LocalTarget(
            generate_output_filename(
                self.input_file,
                self.output_path,
                'parsed'
            )
        )

    def run(self):
        '''  '''
        self._configure()

        f = self.input().open('r')
        data = json.loads(f.read())
        parsed = self.process_response(data)
        if parsed:
            with self.output().open('w') as out_file:
                out_file.write(json.dumps(parsed, indent=4))

    def _configure(self):
        config = parse_yaml(self.yaml_file)
        config = extract_task_config(config, 'Parse')
        self.output_path = config.get('output_directory', '')
        self.params = config.get('params', {})

    def process_response(self, data):
        content = data['content'].encode('unicode_escape')
        url = data['source_url']
        identity = data['identity']

        # if not self.params.get('process_unidentified', False):
        #     # do not generate the generic xml output if it's unknown
        #     print '######### not identified'
        #     return {}

        processor = Processor(identity, content, url)
        if not processor:
            print '######### no processor'
            return {}

        print '################## Parsed #####'

        description = processor.reader.parse_service()
        description['solr_identifier'] = data['digest']
        description['source_url'] = url

        # drop the source for a decent non-xml embedded in my json file
        del data['content']

        data["service_description"] = description
        return data


class TripleTask(luigi.Task):
    yaml_file = luigi.Parameter()
    input_file = luigi.Parameter()

    output_path = ''
    params = {}

    def requires(self):
        return []

    def output(self):
        return luigi.LocalTarget(
            generate_output_filename(
                self.input_file,
                self.output_path,
                'triples',
                '.ttl'
            )
        )

    def run(self):
        '''  '''
        self._configure()

        # f = self.input().open('r')
        # data = json.loads(f.read())

        # the triple cli either outputs the file or posts to the
        # triple store so not sure how this will work
        print '**************', self.input_file

        triples = self.process_response(self.input_file)

        if triples:
            with self.output().open('w') as out_file:
                out_file.write()

    def _configure(self):
        config = parse_yaml(self.yaml_file)
        config = extract_task_config(config, 'Triple')
        self.output_path = config.get('output_directory', '')
        self.params = config.get('params', {})

    def process_response(self, file_path):
        # from the input source/file, get the json and
        # don't do that, just point the cli to the file
        # also this is not the "right" way to do this
        # so, you know, don't do this
        args = ['python', '../semantics/lib/btriple.py', '-p', file_path]

        process = subprocess.Popen(args, stdout=subprocess.PIPE)
        triples = process.communicate()[0]
        print triples
        return triples
