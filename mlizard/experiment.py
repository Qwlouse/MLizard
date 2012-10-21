#!/usr/bin/python
# coding=utf-8
"""
The amazing Experiment class i dreamt up recently.
It should be a kind of ML-Experiment-build-system-checkpointer-...
ROADMAP:
 ### Report
 - write report that is readable by humans and this package
 - it should include the results and all the options as well as the code version
 - make such reports repeatable
 ? maybe have a database to store important facts about experiments,
   so you could easily query what you tried and what resulted

 ### Caching
 - make caching key independent of comments and docstring of the stage
 T Test auto-caching

 ### configuration
 - add logging to configuration
 - add caching to configuration
 V have a kind of config-file-hierarchy so i could define some basic settings
   like paths, logging, caching, ... for my project and experiments only need
   to overwrite some options
 ? maybe even provide means to include other config files?

 ### Stage Repetition
 - count how often a stage was executed and log that
 V automatic repetition of a stage with mean and var of the result
 V make stages easily repeatable with different options
 V make option-sweeps easy
    # maybe like this:
    # with ex.optionset("color") as o:
    #     o.just_call_stage() # and get all the options from the color section
    # for o in ex.optionsets(["color", "gray", "label"]):
    #     o.just_call_stage()
    #
    # We could even implement optionsweep like this
    # for o in ex.optionsweep(["gamma", "C", "lambda"], kernel=["linear", "RBF"])
    #     o.call_stage()

 ### Main method
 - Main should support parameters, loggers, (rnd), many-runs
 - main should also parse command line arguments

 ### Version Control integration
 - find out if current file is git-controlled and if it is checked in, warn otherwise
 - write commit hash to report
 ! automatize rerunning an experiment by checking out the appropriate version and feed the parameters
 ? gather versions of dependencies

 ### Display results
 V should be decoupled from console/pc we are running on
 V figure out how to incorporate plots
 V Make very long stages deliver a stream of data to inspect their behaviour live
 ? maybe start a webserver to watch results
 ? maybe incorporate self-updating plots into ipython-notebook

"""

from __future__ import division, print_function, unicode_literals

from collections import defaultdict
from configobj import ConfigObj
from copy import copy
import inspect
import logging
from matplotlib import pyplot as plt
import numpy as np
from StringIO import StringIO
import time

from caches import CacheStub
from function_helpers import *

__all__ = ['Experiment', 'createExperiment']

RANDOM_SEED_RANGE = 0, 1000000


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

class StageFunction(object):
    def __init__(self, name, f, cache, options, logger, seed):
        self.function = f
        self.logger = logger
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
        # internal state
        self.execution_time = None

    def add_random_arg_to(self, arguments):
        if 'rnd' in self.signature['args']  and 'rnd' not in arguments:
            arguments['rnd'] = self.random

    def add_logger_arg_to(self, arguments):
        if 'logger' in self.signature['args']:
            arguments['logger'] = self.logger

    def execute_function(self, args, kwargs, options):
        # Modify Arguments
        assert_no_unexpected_kwargs(self.signature, kwargs)
        assert_no_duplicate_args(self.signature, args, kwargs)
        arguments = apply_options(self.signature, args, kwargs, options)
        self.add_random_arg_to(arguments)
        key = (self.source, dict(arguments)) # use arguments without logger as cache-key
        self.add_logger_arg_to(arguments)
        assert_no_missing_args(self.signature, arguments)
        # Check for cached version
        try:
            result, result_logs = self.cache[key]
            self.logger.setResult(**result_logs)
            self.logger.info("Retrieved '%s' from cache. Skipping Execution"%self.__name__)
        except KeyError:
        #### Run the function ####
            local_results_handler = ResultLogHandler()
            self.logger.addHandler(local_results_handler)
            start_time = time.time()
            result = self.function(**arguments)
            self.execution_time = time.time() - start_time
            self.logger.info("Completed Stage '%s' in %2.2f sec"%(self.__name__, self.execution_time))
            result_logs = local_results_handler.results
            ##########################
            if self.execution_time > self.caching_threshold:
                self.logger.info("Execution took more than %2.2f sec so we cache the result."%self.caching_threshold)
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


def createExperiment(name = "Experiment", config_file=None, config_string=None, logger=None, seed=None, cache=None):
    # setup logging
    if logger is None:
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        class ResultsLogFilter(object):
            def filter(self, record):
                return record.levelno not in [SET_RESULT_LEVEL, APPEND_RESULT_LEVEL]
        ch.addFilter(ResultsLogFilter())
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        logger.info("No Logger configured: Using generic stdout Logger")

    # reading configuration
    options = ConfigObj(unrepr=True)
    if config_file is not None:
        if isinstance(config_file, basestring) :
            logger.info("Loading config file {}".format(config_file))
            options = ConfigObj(config_file, unrepr=True, encoding="UTF-8")
        elif hasattr(config_file, 'read'):
            logger.info("Reading configuration from file.")
            options = ConfigObj(config_file, unrepr=True, encoding="UTF-8")
    elif config_string is not None:
        logger.info("Reading configuration from string.")
        options = ConfigObj(StringIO(str(config_string)), unrepr=True, encoding="UTF8")

    # get seed for random numbers in experiment
    if seed is None:
        if 'seed' in options:
            seed = options['seed']
        else:
            seed = np.random.randint(*RANDOM_SEED_RANGE)
            logger.warn("No Seed given. Using seed={}. Set in config "
                        "file to repeat experiment".format(seed))

    cache = cache or CacheStub()

    return Experiment(name, logger, options, seed, cache)

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

class OptionContext(object):
    def __init__(self, options, stage_functions):
        self.options = options
        for sf in stage_functions:
            sf_view = StageFunctionOptionsView(sf, options)
            self.__setattr__(sf.func_name, sf_view)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class Experiment(object):
    def __init__(self, name, logger, options, seed, cache):
        self.name = name
        self.logger = logger
        self.options = options
        self.seed = seed
        self.prng = np.random.RandomState(self.seed)
        self.cache = cache
        self.results_handler = ResultLogHandler()
        self.logger.addHandler(self.results_handler)
        self.stages = dict()
        self.plots = []

    def optionset(self, section_name):
        options = copy(self.options)
        options.update(self.options[section_name])
        return OptionContext(options, self.stages.values())


    def stage(self, f):
        """
        Decorator, that converts the function into a stage of this experiment.
        The stage times the execution.

        The stage fills in arguments such that:
        - the original explicit call arguments are preserved
        - missing arguments are filled in by name using options (if possible)
        - default arguments are overridden by options
        - a special 'rnd' parameter is provided containing a
        deterministically seeded numpy.random.RandomState
        - a special 'logger' parameter is provided containing a child of
        the experiment logger with the name of the decorated function
        Errors are still thrown if:
        - you pass an unexpected keyword argument
        - you provide multiple values for an argument
        - after all the filling an argument is still missing"""
        if isinstance(f, StageFunction): # do nothing if it is already a stage
            # TODO: do we need to allow beeing stage of multiple experiments?
            return f
        else :
            stage_name = f.func_name
            stage_logger = self.logger.getChild(stage_name)
            stage_seed = self.prng.randint(*RANDOM_SEED_RANGE)
            stage = StageFunction(stage_name, f, self.cache, self.options, stage_logger, stage_seed)
            self.stages[stage_name] = stage
            return stage

    def plot(self, f):
        """decorator to generate plots"""
        self.plots.append(f)
        return f


    def main(self, f):
        if f.__module__ == "__main__":
            f()
        for p in self.plots:
            p(self.results_handler.results).show()
        plt.show()
        return f