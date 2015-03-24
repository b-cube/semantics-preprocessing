import luigi
import json
from tasks.parse_tasks import ParseTask
from lib.nlp_utils import normalize_subjects
from lib.nlp_utils import is_english
from lib.nlp_utils import collapse_to_bag
from task_helpers import parse_yaml, extract_task_config
from task_helpers import generate_output_filename


'''
text processing tasks
'''


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
                service = service_description.get('service', {})
                if not service:
                    continue

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
                    continue

                for r in remainder:
                    text = r.get('text', '')
                    if text:
                        r['text'] = text if is_english(text) else ""
                # TODO: also don't ignore the attributes (although
                #       these might fall under text that isn't a word)
                service_description['remainder'] = remainder

            if k == "normalize_keywords":
                service = service_description.get('service', {})
                if not service:
                    continue
                subjects = service.get('subject', [])
                if not subjects:
                    continue

                # return split and as a unique list
                service['subject'] = normalize_subjects(subjects, True, True)

                if len(subjects) != len(service['subject']):
                    print '########### UPDATED SUBJECTS: ', subjects, service['subject']

                service_description['service'] = service

        data['service_description'] = service_description
        return data


class BagOfWordsTask(luigi.Task):
    # generate a bag of words with all the cleanup
    def requires(self):
        return

    def output(self):
        return

    def run(self):
        return
