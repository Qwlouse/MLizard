#!/usr/bin/python
# coding=utf-8
from __future__ import division, print_function, unicode_literals

from configobj import ConfigObj
import logging
from StringIO import StringIO

from experiment import Experiment
from mlizard.caches import CacheStub

NO_LOGGER = logging.getLogger('ignore')
NO_LOGGER.disabled = 1

def create_basic_stream_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

package_logger = create_basic_stream_logger('MLizard')

def createExperiment(name = "Experiment", config_file=None, config_string=None,
                     logger=None, seed=None, cache=None):
    # reading configuration
    options = ConfigObj(unrepr=True)
    if config_file is not None:
        if isinstance(config_file, basestring) :
            package_logger.info("Loading config file {}".format(config_file))
            options = ConfigObj(config_file, unrepr=True, encoding="UTF-8")
        elif hasattr(config_file, 'read'):
            package_logger.info("Reading configuration from file.")
            options = ConfigObj(config_file, unrepr=True, encoding="UTF-8")
    elif config_string is not None:
        package_logger.info("Reading configuration from string.")
        options = ConfigObj(StringIO(str(config_string)),
            unrepr=True,
            encoding="UTF8")

    # setup logging
    if logger is None:
        logger = create_basic_stream_logger(name)
        package_logger.info("No Logger configured: Using generic stdout Logger")

    # get seed for random numbers in experiment
    if seed is None:
        if 'seed' in options:
            seed = options['seed']

    cache = cache# or CacheStub()
    results_logger = logging.getLogger("Results")
    return Experiment(name, logger, results_logger, options, cache, seed)


def create_basic_Experiment(seed = 123456):
    name = "TestExperiment"
    options = {}
    cache = CacheStub()
    return Experiment(name, NO_LOGGER, NO_LOGGER, options, cache, seed)