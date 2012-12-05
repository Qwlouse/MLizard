#!/usr/bin/python
# coding=utf-8
from __future__ import division, print_function, unicode_literals

import logging
import time

class Reporter(object):
    def __init__(self, name, message_logger):
        self.experiment_name = name
        self.message_logger = message_logger
        # just use debug, info, ... from message logger
        self.debug = self.message_logger.debug
        self.info = self.message_logger.info
        self.warning = self.message_logger.warning
        self.error = self.message_logger.error
        self.critical = self.message_logger.critical
        self.log = self.message_logger.log
        self.exception = self.message_logger.exception



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



class PlainTextReportFormatter(object):
    def __init__(self):
        self.log_formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
        self.time_format = "%d.%m.%Y %H:%M.%S"

    def format(self, report):
        return """{experiment_name}
=================
started: {start_time}
ended:   {end_time}
seed: {seed}

Stage Summary
-------------
{stage_summary}

Options
-------
{options}

Main Result
-----------
{main_result}

Logged Results
--------------
{logged_results}

Stage Logs
----------
{logs}""".format(
            experiment_name = report.experiment_name,
            start_time = time.strftime(self.time_format, time.gmtime(report.start_time)),
            end_time = time.strftime(self.time_format, time.gmtime(report.end_time)),
            seed = report.seed,
            options = "\n".join("{} = {}".format(k, v)
                                for k,v in report.options.items()),
            stage_summary = "\n".join("%d x %s : %s"%(len(s['execution_times']),
                                                      s['name'],
                                                      ", ".join('%2.2fs'%t for t in s['execution_times'])) for s in report.stage_summary),
            main_result = report.main_result,
            logged_results = "\n".join("{} = {}".format(k, v)
                                    for k,v in report.logged_results.items()),
            logs = "\n".join(self.log_formatter.format(l)
                             for l in report.log_records)
        )