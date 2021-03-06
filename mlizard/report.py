#!/usr/bin/python
# coding=utf-8
from __future__ import division, print_function, unicode_literals
import datetime
import time
from jinja2 import PackageLoader

IDLE, STARTED, STAGE_RUNNING, FINISHED = range(4)

class ExperimentObserver(object):
    def experiment_created_event(self, name, options):
        pass

    def experiment_mainfile_found_event(self, mainfile, doc):
        pass

    def experiment_started_event(self, start_time, seed, args, kwargs):
        pass

    def experiment_completed_event(self, stop_time, result):
        pass

    def stage_created_event(self, name, doc, source, signature):
        pass

    def stage_started_event(self, name, start_time, arguments):
        pass

    def stage_completed_event(self, stop_time):
        pass

class CompleteReporter(ExperimentObserver):
    def __init__(self):
        self.experiment_entry = dict()
        self.stack = [self.experiment_entry]

    def experiment_created_event(self, name, options):
        self.experiment_entry['name'] = name
        self.experiment_entry['options'] = options
        self.experiment_entry['stages'] = {}

    def experiment_mainfile_found_event(self, mainfile, doc):
        self.experiment_entry['mainfile'] = mainfile
        self.experiment_entry['doc'] = doc

    def experiment_started_event(self, start_time, seed, args, kwargs):
        self.experiment_entry['start_time'] = start_time
        self.experiment_entry['seed'] = seed
        self.experiment_entry['args'] = args
        self.experiment_entry['kwargs'] = kwargs
        self.experiment_entry['called'] = []

    def experiment_completed_event(self, stop_time, result):
        self.experiment_entry['stop_time'] = stop_time
        self.experiment_entry['execution_time'] = stop_time - self.experiment_entry['start_time']
        self.experiment_entry['result'] = result

    def stage_created_event(self, name, doc, source, signature):
        stage_entry = dict(
            source=source,
            doc=doc,
            signature=signature)
        self.experiment_entry['stages'][name] = stage_entry

    def stage_started_event(self, name, start_time, arguments):
        stage_entry = dict(
            name=name,
            start_time=start_time,
            arguments=arguments,
            called=[]
            )
        self.stack[-1]['called'].append(stage_entry)
        self.stack.append(stage_entry)

    def stage_completed_event(self, stop_time):
        stage_entry = self.stack.pop()
        stage_entry['stop_time'] = stop_time
        stage_entry['execution_time'] = stop_time - stage_entry['start_time']

class CouchDBReporter(CompleteReporter):
    def __init__(self, url=None, db_name='mlizard_experiments'):
        super(CouchDBReporter, self).__init__()
        import couchdb
        if url:
            couch = couchdb.Server(url)
        else:
            couch = couchdb.Server()
        if db_name in couch:
            self.db = couch[db_name]
        else:
            self.db = couch.create(db_name)

    def save(self):
        self.db.save(self.experiment_entry)

    def experiment_created_event(self, name, options):
        CompleteReporter.experiment_created_event(self, name, options)
        self.save()

    def experiment_mainfile_found_event(self, mainfile, doc):
        CompleteReporter.experiment_mainfile_found_event(self, mainfile, doc)
        self.save()

    def experiment_started_event(self, start_time, seed, args, kwargs):
        CompleteReporter.experiment_started_event(self, start_time, seed, args, kwargs)
        self.save()

    def experiment_completed_event(self, stop_time, result):
        CompleteReporter.experiment_completed_event(self, stop_time, result)
        self.save()

    def stage_created_event(self, name, doc, source, signature):
        CompleteReporter.stage_created_event(self, name, doc, source, signature)
        self.save()

    def stage_started_event(self, name, start_time, arguments):
        CompleteReporter.stage_started_event(self, name, start_time, arguments)
        self.save()

    def stage_completed_event(self, stop_time):
        CompleteReporter.stage_completed_event(self, stop_time)
        self.save()

def _datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return time.strftime(format, time.localtime(value))

def _timedeltaformat(value):
    return str(datetime.timedelta(seconds=value))

class JinjaReporter(CompleteReporter):
    def __init__(self):
        super(JinjaReporter, self).__init__()
        from jinja2 import Environment
        self.env = Environment(loader=PackageLoader('mlizard', 'templates'))
        self.env.filters['datetime'] = _datetimeformat
        self.env.filters['timedelta'] = _timedeltaformat

    def experiment_completed_event(self, stop_time, result):
        CompleteReporter.experiment_completed_event(self, stop_time, result)
        t = self.env.get_template("rstReport.jinja2")
        r = t.render(experiment=self.experiment_entry)
        if 'report_filename' in self.experiment_entry:
            path = self.experiment_entry['report_filename']
        else:
            # replace the trailing '.py' with '.report'
            path = self.experiment_entry['mainfile'][:-3] + '.report'
        with open(path, 'w') as outf:
            outf.write(r)

