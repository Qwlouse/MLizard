#!/usr/bin/python
# coding=utf-8
from __future__ import division, print_function, unicode_literals

import logging
import time

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
            stage_summary = "\n".join(str(s) for s in report.stage_summary),
            main_result = report.main_result,
            logged_results = "\n".join("{} = {}".format(k, v)
                                    for k,v in report.logged_results.items()),
            logs = "\n".join(self.log_formatter.format(l)
                             for l in report.log_records)
        )