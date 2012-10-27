#!/usr/bin/python
# coding=utf-8
# This file is part of the MLizard library published under the GPL3 license.
# Copyright (C) 2012  Klaus Greff
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
docstring
"""
from __future__ import division, print_function, unicode_literals
import numpy as np
import inspect
from function_helpers import *
import time
import log
from mlizard.log import StageFunctionLoggerFacade

class StageFunction(object):
    def __init__(self, name, f, cache, options, message_logger, results_logger, seed):
        self.function = f
        self.message_logger = message_logger
        self.results_logger = results_logger
        self.random = np.random.RandomState(seed)
        self.cache = cache
        self.options = options
        # preserve meta_information
        self.__name__ = name
        self.func_name = name
        self.__doc__ = f.__doc__
        # extract extra info
        self.source = str(inspect.getsource(f))
        self.signature = get_signature(f)
        # some configuration
        self.caching_threshold = 2 # seconds
        self.do_cache_results = True
        # internal state
        self.execution_time = None

    def add_random_arg_to(self, arguments):
        if 'rnd' in self.signature['args']  and 'rnd' not in arguments:
            arguments['rnd'] = self.random

    def add_logger_arg_to(self, arguments):
        l = StageFunctionLoggerFacade(self.message_logger, self.results_logger)
        if 'logger' in self.signature['args']:
            arguments['logger'] = l
        return l

    def execute_function(self, args, kwargs, options):
        # Modify Arguments
        assert_no_unexpected_kwargs(self.signature, kwargs)
        assert_no_duplicate_args(self.signature, args, kwargs)
        arguments = apply_options(self.signature, args, kwargs, options)
        self.add_random_arg_to(arguments)
        key = (self.source, dict(arguments)) # use arguments without logger as cache-key
        log_facade = self.add_logger_arg_to(arguments)
        assert_no_missing_args(self.signature, arguments)
        # do we want to cache?
        if self.cache and self.do_cache_results:
            # Check for cached version
            try:
                result, result_logs = self.cache[key]
                log_facade.set_result(**result_logs)
                self.message_logger.info("Retrieved '%s' from cache. Skipping Execution"%self.__name__)
                return result
            except KeyError:
                pass

        #### Run the function ####
        local_results_handler = log.ResultLogHandler()
        self.results_logger.addHandler(local_results_handler)
        start_time = time.time()
        result = self.function(**arguments)
        self.execution_time = time.time() - start_time
        self.message_logger.info("Completed Stage '%s' in %2.2f sec"%(self.__name__, self.execution_time))
        result_logs = local_results_handler.results
        ##########################

        if self.cache and self.do_cache_results and self.execution_time > self.caching_threshold:
            self.message_logger.info("Execution took more than %2.2f sec so we cache the result."%self.caching_threshold)
            self.cache[key] = result, result_logs
        return result

    def __call__(self, *args, **kwargs):
        return self.execute_function(args, kwargs, self.options)

    def __hash__(self):
        return hash(self.source)


class StageFunctionOptionsView(object):
    def __init__(self, stage_func, options):
        self.options = options
        self.func = stage_func

    def __call__(self, *args, **kwargs):
        return self.func.execute_function(args, kwargs, self.options)
