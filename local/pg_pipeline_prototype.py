import luigi
import sqlalchemy as sqla
from sqlalchemy.orm import sessionmaker, mapper
from sqlalchemy import Table, MetaData, Column, Integer, String, DateTime
from datetime import datetime


metadata = MetaData()


class TaskA(luigi.Task):
    '''
    take the file, read the string and insert
    into postgres, get the new id and save to the output
    '''
    input_file = luigi.Parameter()

    def requires(self):
        return None

    def output(self):
        return luigi.LocalTarget('taska.txt')

    def run(self):
        '''  '''
        with open(self.input_file, 'r') as in_file:
            data = in_file.read()

        new_data = self._insert(data)

        with self.output().open('w') as out_file:
            out_file.write('{0}'.format(new_data))

    def _insert(self, s):
        sa = LocalSqla()
        new_id = sa.insert(s)
        return new_id


class TaskB(luigi.Task):
    '''
    get the id from the input target, query postgres,
    update with a timestamp or something, save target
    '''
    input_file = luigi.Parameter()

    def requires(self):
        return TaskA(input_file=self.input_file)

    def output(self):
        return luigi.LocalTarget('taskb.txt')

    def run(self):
        '''  '''

        with self.input().open('r') as in_file:
            data = in_file.read()

        self._update(data)

        with self.output().open('w') as out_file:
            out_file.write('updated')

    def _update(self, identifier):
        sa = LocalSqla()
        sa.update(identifier)


class LocalSqla():
    def __init__(self):
        # set up the connection
        engine = sqla.create_engine('postgresql://tester:abcd123@localhost/workflow-test')
        session = sessionmaker()
        session.configure(bind=engine)

        self.session = session()

    def query(self, value):
        # execute the select
        return self.session.query(ObjectTable).filter(ObjectTable.id == value).first()

    def insert(self, value):
        # update the timestamp
        obj = ObjectTable(value)
        self.session.add(obj)
        self.session.commit()
        self.session.flush()
        return obj.id

    def update(self, identifier):
        # this is just going to add a timestamp
        obj = self.query(identifier)
        if not obj:
            return

        obj.updated = datetime.now()
        self.session.commit()

object_table = Table(
    'objects',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(50)),
    Column('updated', DateTime(True))
)


class ObjectTable(object):
    def __init__(self, name):
        self.name = name

mapper(ObjectTable, object_table)


if __name__ == '__main__':
    # to run: python pg_pipeline_prototype.py --local-scheduler TaskB --TaskB-input-file psql.txt
    # not sure what's going on with the local targets and passing input()s except it was passed
    # through the builder as a list? probs.
    luigi.run()
