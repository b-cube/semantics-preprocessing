import luigi
from lib.nlp_utils import normalize_subjects


'''
text processing tasks
'''


class KeywordTask(luigi.Task):
    # execute the keyword normalization
    

    def requires(self):
        return

    def output(self):
        return

    def run(self):
        return


class BagOfWordsTask(luigi.Task):
    # gneerate a bag of words with all the cleanup
    def requires(self):
        return

    def output(self):
        return

    def run(self):
        return
