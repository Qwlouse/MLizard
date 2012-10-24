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

LoggerClass = logging.getLoggerClass()
SET_RESULT_LEVEL = 100
APPEND_RESULT_LEVEL = 101
class ExperimentLogger(logging.Logger):
    def __init__(self, name, level=logging.NOTSET):
        super(ExperimentLogger, self).__init__(name, level=level)

    def setResult(self, **kwargs):
        self._log(SET_RESULT_LEVEL, "set result: %(set_dict)s", None, extra={"set_dict" : kwargs})

    def appendResult(self, **kwargs):
        self._log(APPEND_RESULT_LEVEL, "append result: %(append_dict)s", None, extra= {"append_dict" : kwargs})

logging.setLoggerClass(ExperimentLogger)



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