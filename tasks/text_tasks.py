import luigi
import json
import re
from tasks.parse_tasks import ParseTask
from lib.parsers import Parser
from lib.nlp_utils import normalize_subjects
from lib.nlp_utils import is_english
from lib.nlp_utils import collapse_to_bag
from lib.nlp_utils import remove_punctuation
from lib.nlp_utils import remove_stopwords
from lib.nlp_utils import remove_mimetypes
from lib.nlp_utils import tokenize_text
from task_helpers import parse_yaml, extract_task_config
from task_helpers import generate_output_filename
from task_helpers import read_data


'''
text processing tasks
'''


def _normalize_keywords(service_description):
    service = service_description.get('service', {})
    if not service:
        return service_description
    subjects = service.get('subject', [])
    if not subjects:
        return service_description

    # return split and as a unique list
    service['subject'] = normalize_subjects(subjects, True, True)
    service_description['service'] = service
    return service_description


class TextPreprocessingTask(luigi.Task):
    yaml_file = luigi.Parameter()
    input_file = luigi.Parameter()

    output_path = ''
    tasks = {}

    def requires(self):
        return ParseTask(input_file=self.input_file, yaml_file=self.yaml_file)

    def output(self):
        return luigi.LocalTarget(
            generate_output_filename(
                self.input_file,
                self.output_path,
                'processed'
            )
        )

    def run(self):
        self._configure()

        f = self.input().open('r')
        data = json.loads(f.read())

        processed = self.process_response(data)

        if processed:
            with self.output().open('w') as out_file:
                out_file.write(json.dumps(processed, indent=4))

    def _configure(self):
        config = parse_yaml(self.yaml_file)
        config = extract_task_config(config, 'TextPreprocessing')
        self.output_path = config.get('output_directory', '')
        self.tasks = config.get('tasks', {})

    def process_response(self, data):
        if not self.tasks:
            return data

        service_description = data.get('service_description', {})
        if not service_description:
            return data

        for k, v in self.tasks.iteritems():
            # so this need to go in the order of the
            # items in the task list (most of the time)
            # and we are often simply running based on
            # the key value as a basic trigger
            if k == 'detect_language':
                service_description = self._detect_language(service_description)

            if k == "normalize_keywords":
                service_description = _normalize_keywords(service_description)

        data['service_description'] = service_description
        return data

    def _detect_language(self, service_description):
        service = service_description.get('service', {})
        if not service:
            return service_description

        # TODO: don't ignore the endpoints
        for sk, sv in service.iteritems():
            if sk == 'endpoints':
                continue

            service[sk] = [s for s in sv if is_english(s)]

            if len(sv) != len(service[sk]):
                print 'NOT ENGLISH: ', sv, service[sk]

        service_description['service'] = service

        remainder = service_description.get('remainder', [])
        if not remainder:
            return service_description

        for r in remainder:
            text = r.get('text', '')
            if text:
                r['text'] = text if is_english(text) else ""
        # TODO: also don't ignore the attributes (although
        #       these might fall under text that isn't a word)
        service_description['remainder'] = remainder

        return service_description


class BagOfWordsFromParsedTask(luigi.Task):
    # generate a bag of words with all the cleanup
    # from an already parsed json file (this is the one task)

    '''
    normalize keywords
    collapse bag (for more processing)
    remove mimetypes
    remove punctuation
    tokenize words
    remove stopwords
    parts of speech tagging
    lemmatize/stem
    extract by pos (noun/verb only? depending on lemma vs stem)
    collapse bag (return none if bag length < N words)
    '''

    yaml_file = luigi.Parameter()
    input_file = luigi.Parameter()

    output_path = ''
    tasks = {}
    minimum_wordcount = 10

    def requires(self):
        return []

    def output(self):
        return luigi.LocalTarget(
            generate_output_filename(
                self.input_file,
                self.output_path,
                'bow'
            )
        )

    def run(self):
        self._configure()

        data = read_data(self.input_file)
        bagofwords = self.process_response(data)

        with self.output().open('w') as out_file:
            out_file.write(bagofwords)

    def _configure(self):
        config = parse_yaml(self.yaml_file)
        config = extract_task_config(config, 'BagOfWordsFromParsed')
        self.output_path = config.get('output_directory', '')
        self.tasks = config.get('tasks', {})
        self.minimum_wordcount = config.get('minimum_wordcount', self.minimum_wordcount)

    def process_response(self, data):
        service_description = data.get('service_description', {})
        if not service_description:
            return ''

        if 'normalize_keywords' in self.tasks:
            service_description = _normalize_keywords(service_description)

        bag = collapse_to_bag(service_description, True)

        for k, v in self.tasks.iteritems():
            if k == 'remove_mimetypes':
                bag = remove_mimetypes(bag)
            elif k == 'remove_punctuation':
                bag = remove_punctuation(bag)
            elif k == 'remove_stopwords':
                bag = remove_stopwords(bag)

        return bag


class BagOfWordsFromXML(luigi.Task):
    yaml_file = luigi.Parameter()
    input_file = luigi.Parameter()

    output_path = ''
    tasks = {}
    minimum_wordcount = 10
    include_structure = True

    def requires(self):
        return []

    def output(self):
        return luigi.LocalTarget(
            generate_output_filename(
                self.input_file,
                self.output_path,
                'bow'
            )
        )

    def run(self):
        self._configure()

        data = read_data(self.input_file)
        bagofwords = self.process_response(data)

        with self.output().open('w') as out_file:
            out_file.write(bagofwords)

    def _configure(self):
        config = parse_yaml(self.yaml_file)
        config = extract_task_config(config, 'BagOfWordsFromXML')
        self.output_path = config.get('output_directory', '')
        self.tasks = config.get('tasks', {})
        self.minimum_wordcount = config.get('minimum_wordcount', self.minimum_wordcount)
        self.include_structure = config.get('include_structure', self.include_structure)

    def process_response(self, data):
        '''
        data here is just the raw_content from the cleaned result set

        strip punctuation (modified version)
        tokenize
        strip stopwords
        '''

        def _strip_punctuation(text):
            simple_pattern = r'[;|>+:=.,<?(){}`\'"]'
            text = re.sub(simple_pattern, ' ', text)
            return text.replace("/", ' ')

        content = data['content']

        if self.include_structure:
            # include the xml tags, etc
            # note: this uses a different punctuation set
            bow = _strip_punctuation(content)
            words = tokenize_text(bow)
            return ' '.join(remove_stopwords(words))
        else:
            # pull out the text only
            parser = Parser(content)
            all_text = parser.find_nodes()

            # collapse to just text and attributes.text values
            bow = ''
            bow += ' '.join([a.get('text' '') for a in all_text])

            atts = [a.get('attributes', []) for a in all_text]
            bow += ' '.join([a.get('text' '') for a in atts])

            bow = remove_punctuation(bow)
            words = tokenize_text(bow)
            bow = ' '.join(remove_stopwords(words))
