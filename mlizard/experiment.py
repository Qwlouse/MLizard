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
import inspect
import os
import log
from matplotlib import pyplot as plt
import numpy as np
import time


from stage import StageFunctionOptionsView, StageFunction

__all__ = ['Experiment']

RANDOM_SEED_RANGE = 0, 1000000

class Experiment(object):
    def __init__(self, name, message_logger, results_logger, options,
                 cache, observers=None, seed=None):
        self.name = name
        self.observers = observers or []
        self.message_logger = message_logger
        self.results_logger = results_logger
        self.options = options
        self.cache = cache
        self.results_handler = log.ResultLogHandler()
        self.results_logger.addHandler(self.results_handler)
        self.stages = dict()
        self.main_stage = None
        self.plot_functions = []#TODO move to some observer
        self.live_plots = []#TODO move to some observer

        if seed is None:
            seed = np.random.randint(*RANDOM_SEED_RANGE)
            message_logger.warn("No Seed given. Using seed={}. Set in config "
                                "file to repeat experiment".format(seed))
        self.seed = seed
        self.prng = np.random.RandomState(seed)
        self.emit_created()

    ################### Observable interface ###################################
    def add_observer(self, obs):
        if not obs in self.observers:
            self.observers.append(obs)

    def remove_observer(self, obs):
        if obs in self.observers:
            self.observers.remove(obs)

    def emit_created(self):
        for o in self.observers:
            try:
                o.experiment_created_event(self.name, self.options)
            except AttributeError:
                pass

    def emit_started(self, args, kwargs):
        start_time = time.time()
        for o in self.observers:
            try:
                o.experiment_started_event(start_time, self.seed, args, kwargs)
            except AttributeError:
                pass

    def emit_completed(self, result):
        stop_time = time.time()
        for o in self.observers:
            try:
                o.experiment_completed_event(stop_time, result)
            except AttributeError:
                pass

    ################### Option set methods #####################################
    def optionset(self, section_name):
        options = copy(self.options)
        options.update(self.options[section_name])
        return OptionContext(options, self.stages.values())

    def optionsets(self, section_names):
        for sn in section_names:
            o = self.optionset(sn)
            o.__enter__()
            yield o
            o.__exit__(None, None, None)

    def convert_to_stage_function(self, f):
        if isinstance(f, StageFunction): # do nothing if it is already a stage
            # do we need to allow being stage of multiple experiments?
            return f
        else :
            stage_name = f.func_name
            stage_msg_logger = self.message_logger.getChild(stage_name)
            stage_results_logger = self.results_logger.getChild(stage_name)
            stage_seed = self.prng.randint(*RANDOM_SEED_RANGE)
            return StageFunction(stage_name, f, self.options, stage_msg_logger,
                stage_results_logger, stage_seed, self.observers, self.cache)

    ################### Adding Stage functions #################################
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
        - after all the filling, an argument is still missing"""
        stage = self.convert_to_stage_function(f)
        self.stages[stage.__name__] = stage
        return stage

    def main(self, f):
        assert self.main_stage is None, "Only one main stage is allowed!"
        self.main_stage = self.convert_to_stage_function(f)
        main_file = inspect.getabsfile(f)
        self.set_paths(main_file)
        if f.__module__ == "__main__":
            import sys
            args = sys.argv[1:]
            ######## run main #########
            report = self(*args)
            ###########################
            # show all plots and wait
            plt.ioff()
            plt.show()
            sys.exit(0)
        return self

    ############################ Calling #######################################
    def __call__(self, *args, **kwargs):
        self.emit_started(args, kwargs)

        ######## call stage #########
        result = self.main_stage.execute_function(args, kwargs, self.options)
        #############################

        #report.logged_results = self.results_handler.results

        # plotting
        plots = []
        for p in self.plot_functions:
            fig = p(self.results_handler.results)
            fig.draw()
            plots.append(fig)
        #report.plots = plots
        return self.emit_completed(result)

    ############################ To Move #######################################
    def plot(self, f): #TODO move to some observer
        """decorator to generate plots"""
        self.plot_functions.append(f)
        return f

    def live_plot(self, f): #TODO move to some observer
        if not inspect.isgeneratorfunction(f):
            raise TypeError("Live plots must be generator functions!")
        self.live_plots.append(f)
        self.results_handler.add_plot(f)

    def set_paths(self, main_file): #TODO move to some observer
        if 'results_dir' in self.options:
            self.results_dir = self.options.results_dir
        else :
            self.results_dir = os.path.dirname(main_file)
        if not os.path.exists(self.results_dir):
            self.message_logger.warn("results_dir '%s' does not exist. No results will be written.", self.results_dir)
            self.results_dir = None




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

    def keys(self):
        return self.options.keys()

    def __getitem__(self, item):
        return self.options[item]
