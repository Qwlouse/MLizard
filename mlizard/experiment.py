#!/usr/bin/python
# coding=utf-8
# This file is part of the MLizard library published under the GPL3 license.
# Copyright (C) 2012  Klaus Greff
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
The amazing Experiment class i dreamt up recently.
It should be a kind of ML-Experiment-build-system-checkpointer-...
ROADMAP:
 ### Report
 ? maybe have a database to store important facts about experiments,
   so you could easily query what you tried and what resulted

 ### Caching
 - make caching key independent of comments and docstring of the stage

 ### configuration
 V have a kind of config-file-hierarchy so i could define some basic settings
   like paths, logging, caching, ... for my project and experiments only need
   to overwrite some options
 ? maybe even provide means to include other config files?

 ### Stage Repetition
 - count how often a stage was executed and log that
 V automatic repetition of a stage with mean and var of the result

 ### Main method
 - main should also parse command line arguments

 ### Version Control integration
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


from configobj import ConfigObj
from copy import copy
import log
import logging
from matplotlib import pyplot as plt
import numpy as np
from StringIO import StringIO

from caches import CacheStub
from stage import StageFunctionOptionsView, StageFunction

__all__ = ['Experiment', 'createExperiment']

RANDOM_SEED_RANGE = 0, 1000000




def createExperiment(name = "Experiment", config_file=None, config_string=None, logger=None, seed=None, cache=None):
    # setup logging
    if logger is None:
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
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

    cache = cache# or CacheStub()
    results_logger = logging.getLogger("Results")
    prng = np.random.RandomState(seed)
    return Experiment(name, logger, results_logger, options, prng, cache)



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
    def __init__(self, name, message_logger, results_logger, options, prng, cache):
        self.name = name
        self.message_logger = message_logger
        self.results_logger = results_logger
        self.options = options
        self.prng = prng
        self.cache = cache
        self.results_handler = log.ResultLogHandler()
        self.results_logger.addHandler(self.results_handler)
        self.stages = dict()
        self.plots = []

    def optionset(self, section_name):
        options = copy(self.options)
        options.update(self.options[section_name])
        return OptionContext(options, self.stages.values())

    def convert_to_stage_function(self, f):
        if isinstance(f, StageFunction): # do nothing if it is already a stage
            # do we need to allow beeing stage of multiple experiments?
            return f
        else :
            stage_name = f.func_name
            stage_msg_logger = self.message_logger.getChild(stage_name)
            stage_results_logger = self.results_logger.getChild(stage_name)
            stage_seed = self.prng.randint(*RANDOM_SEED_RANGE)
            return StageFunction(stage_name, f, self.cache, self.options,
                stage_msg_logger, stage_results_logger, stage_seed)

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
        stage = self.convert_to_stage_function(f)
        self.stages[stage.__name__] = stage
        return stage

    def plot(self, f):
        """decorator to generate plots"""
        self.plots.append(f)
        return f


    def main(self, f):
        main_stage = self.convert_to_stage_function(f)
        if f.__module__ == "__main__":
            main_stage()
            for p in self.plots:
                p(self.results_handler.results).show()
            plt.ioff()
            plt.show()
        return main_stage