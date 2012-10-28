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
 ! automatize rerunning an experiment by checking out the appropriate version
   and feed the parameters
 ? gather versions of dependencies

 ### Display results
 V should be decoupled from console/pc we are running on
 ? maybe start a webserver to watch results
"""

from __future__ import division, print_function, unicode_literals

from copy import copy
import log
from matplotlib import pyplot as plt
import numpy as np
import time

from report import Report, PlainTextReportFormatter
from stage import StageFunctionOptionsView, StageFunction

__all__ = ['Experiment']

RANDOM_SEED_RANGE = 0, 1000000

class Experiment(object):
    def __init__(self, name, message_logger, results_logger, options, cache,
                 seed = None):
        self.name = name
        self.message_logger = message_logger
        self.results_logger = results_logger
        self.options = options
        self.cache = cache
        self.results_handler = log.ResultLogHandler()
        self.results_logger.addHandler(self.results_handler)
        self.stages = dict()
        self.main_stage = None
        self.plot_functions = []

        if seed is None:
            seed = np.random.randint(*RANDOM_SEED_RANGE)
            message_logger.warn("No Seed given. Using seed={}. Set in config "
                                "file to repeat experiment".format(seed))
        self.seed = seed
        self.prng = np.random.RandomState(seed)

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
        self.plot_functions.append(f)
        return f


    def main(self, f):
        assert self.main_stage is None, "Only one main stage is allowed!"
        self.main_stage = self.convert_to_stage_function(f)
        if f.__module__ == "__main__":
            import sys
            args = sys.argv[1:]
            ######## run main #########
            report = self(*args)
            ###########################
            plt.ioff()
            plt.show()
            formatter = PlainTextReportFormatter()
            print(formatter.format(report))
            sys.exit(0)
        return self

    def __call__(self, *args, **kwargs):
        report = Report(self.name)
        self.message_logger.addHandler(report)
        ######## call stage #########
        result = self.main_stage.execute_function(args, kwargs, self.options)
        #############################
        self.message_logger.removeHandler(report)
        report.seed = self.seed
        report.options = self.options
        report.main_result = result
        report.logged_results = self.results_handler.results
        report.stage_summary = [{'name' : s.__name__,
                                 'execution_times' : s.execution_times}
                                for s in self.stages.values()]
        # plotting
        plots = []
        for p in self.plot_functions:
            fig = p(self.results_handler.results)
            fig.draw()
            plots.append(fig)
        report.plots = plots
        report.end_time = time.time()
        return report

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