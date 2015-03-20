import luigi
from lib.nlp_utils import normalize_subjects
from lib.nlp_utils import is_english
from lib.nlp_utils import collapse_to_bag


'''
text processing tasks
'''


class LanguageIdentificationTask(luigi.Task):
    input_path = luigi.Parameter()

    def requires(self):
        return

    def output(self):
        return

    def run(self):
        return


class KeywordTask(luigi.Task):
    # execute the keyword normalization
    input_path = luigi.Parameter()

    def requires(self):
        return

    def output(self):
        return

    def run(self):
        return

    def process_response(self, data):
        description = data.get('service_description', {})
        if not description:
            return data

        subjects = description.get('subject', [])
        if not subjects:
            return data

        subjects = normalize_subjects(subjects, True)
        description.update({"subject": subjects})
        data.update({"service_description": description})
        return data


class BagOfWordsTask(luigi.Task):
    # gneerate a bag of words with all the cleanup
    def requires(self):
        return

    def output(self):
        return

    def run(self):
        return
