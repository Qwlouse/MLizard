#!/usr/bin/python
# coding=utf-8
from __future__ import division, print_function, unicode_literals

import logging
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

    def stage_started_event(self, name, start_time, arguments, cache_key):
        pass

    def stage_completed_event(self, stop_time, result, result_logs, from_cache):
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
        self.experiment_entry['result'] = result

    def stage_created_event(self, name, doc, source, signature):
        stage_entry = dict(
            source=source,
            doc=doc,
            signature=signature)
        self.experiment_entry['stages'][name] = stage_entry

    def stage_started_event(self, name, start_time, arguments, cache_key):
        stage_entry = dict(
            name=name,
            start_time=start_time,
            arguments=arguments,
            cache_key=cache_key,
            called=[]
            )
        self.stack[-1]['called'].append(stage_entry)
        self.stack.append(stage_entry)

    def stage_completed_event(self, stop_time, result, result_logs, from_cache):
        stage_entry = self.stack.pop()
        stage_entry['stop_time'] = stop_time
        stage_entry['result'] = result
        stage_entry['result_logs'] = result_logs
        stage_entry['from_cache'] = from_cache

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

    def stage_started_event(self, name, start_time, arguments, cache_key):
        CompleteReporter.stage_started_event(self, name, start_time, arguments, cache_key)
        self.save()

    def stage_completed_event(self, stop_time, result, result_logs, from_cache):
        CompleteReporter.stage_completed_event(self, stop_time, result, result_logs, from_cache)
        self.save()


class JinjaReporter(CompleteReporter):
    def write(self, path):
        def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
            return time.strftime(format, time.localtime(value))

        from jinja2 import Environment
        env = Environment(loader=PackageLoader('mlizard', 'templates'))
        env.filters['datetime'] = datetimeformat
        t = env.get_template("PlainReport.jinja2")

        r = t.render(experiment=self.experiment_entry)
        with open(path, 'w') as outf:
            outf.write(r)

    def experiment_completed_event(self, stop_time, result):
        CompleteReporter.experiment_completed_event(self, stop_time, result)
        self.write("report.rst")

