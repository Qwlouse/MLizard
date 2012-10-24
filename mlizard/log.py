#!/usr/bin/python
# coding=utf-8
# This file is part of the MLizard library published under the GPL3 license.
# Copyright (C) 2012  Klaus Greff
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Logging functionality for experiments
"""
from __future__ import division, print_function, unicode_literals
import logging
from collections import defaultdict

SET_RESULT_LEVEL = 100
APPEND_RESULT_LEVEL = 110

class StageFunctionLoggerFacade(object):
    def __init__(self, message_logger, results_logger):
        self.message_logger = message_logger
        # just use debug, info, ... from message logger
        self.debug = self.message_logger.debug
        self.info = self.message_logger.info
        self.warning = self.message_logger.warning
        self.error = self.message_logger.error
        self.critical = self.message_logger.critical
        self.log = self.message_logger.log
        self.exception = self.message_logger.exception

        self.results_logger = results_logger

    def set_result(self, **kwargs):
        self.results_logger._log(SET_RESULT_LEVEL, "set result: %(set_dict)s", None, extra={"set_dict" : kwargs})

    def appendResult(self, **kwargs):
        self.results_logger._log(APPEND_RESULT_LEVEL, "append result: %(append_dict)s", None, extra= {"append_dict" : kwargs})




class ResultLogHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super(ResultLogHandler, self).__init__(level=level)
        self.results = defaultdict(list)

    def filter(self, record):
        return record.levelno in [SET_RESULT_LEVEL, APPEND_RESULT_LEVEL]

    def handle(self, record):
        if record.levelno == SET_RESULT_LEVEL:
            self.results.update(record.set_dict)
        elif record.levelno == APPEND_RESULT_LEVEL:
            for k, v in record.append_dict.items():
                self.results[k].append(v)