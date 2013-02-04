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

    def experiment_started_event(self, start_time, seed, args, kwargs):
        pass

    def experiment_completed_event(self, stop_time, result):
        pass

    def stage_created_event(self, name, source, signature):
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

    def experiment_started_event(self, start_time, seed, args, kwargs):
        self.experiment_entry['start_time'] = start_time
        self.experiment_entry['seed'] = seed
        self.experiment_entry['args'] = args
        self.experiment_entry['kwargs'] = kwargs
        self.experiment_entry['called'] = []

    def experiment_completed_event(self, stop_time, result):
        self.experiment_entry['stop_time'] = stop_time
        self.experiment_entry['result'] = result

    def stage_created_event(self, name, source, signature):
        stage_entry = dict(
            source=source,
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

    def experiment_started_event(self, start_time, seed, args, kwargs):
        CompleteReporter.experiment_started_event(self, start_time, seed, args, kwargs)
        self.save()

    def experiment_completed_event(self, stop_time, result):
        CompleteReporter.experiment_completed_event(self, stop_time, result)
        self.save()

    def stage_created_event(self, name, source, signature):
        CompleteReporter.stage_created_event(self, name, source, signature)
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


class Reporter(logging.Handler):
    def __init__(self, name, message_logger):
        super(Reporter, self).__init__()
        self.experiment_name = name
        self.message_logger = message_logger
        self.log_records = []
        self.mode = IDLE
        # provide debug, info, ... from message_logger
        self.debug = self.message_logger.debug
        self.info = self.message_logger.info
        self.warning = self.message_logger.warning
        self.error = self.message_logger.error
        self.critical = self.message_logger.critical
        self.log = self.message_logger.log
        self.exception = self.message_logger.exception

    def experiment_started(self, options, seed):
        self.ex_start_time = time.time()
        self.options = options
        self.seed = seed
        self.log_records = []
        self.mode = STARTED

    def experiment_completed(self):
        self.mode = FINISHED
        self.ex_stop_time = time.time()

    def emit(self, record):
        self.log_records.append(record)

    def create_report(self):
        report = Report(self.experiment_name)
        self.message_logger.addHandler(report)
        return report

    def get_message_logger_for(self, stagename):
        return self.message_logger.get_child(stagename)



class Report(logging.Handler):
    def __init__(self, experiment_name):
        super(Report, self).__init__()
        self.experiment_name = experiment_name
        self.start_time = time.time()
        self.end_time = 0.
        self.seed = None
        self.options = {}
        self.stage_summary = []
        self.main_result = None
        self.logged_results = {}
        self.log_records = []
        self.plots = []

    def experiment_started(self, options, seed):
        self.options = options
        self.seed = seed


    def emit(self, record):
        self.log_records.append(record)


