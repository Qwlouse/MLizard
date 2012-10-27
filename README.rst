=======
MLizard
=======

Python machine learning infrastructure project. The idea of MLizard is to make
it easy to run lots of different experiments on lots of different options,
constantly changing or exchanging parts of the process, without loosing track
of what you did, when you did it, how you did it, what came out of it, which
files are connected to it and so on. So this is how it looks like::

    """
    # for this demo we use the docstring as config
    alpha = 0.7
    beta = 7
    gamma = "Foo"
    """
    # at the beginning of the file we create an experiment
    from mlizard.experiment import createExperiment
    ex = createExperiment("Demo", config_string=__doc__)

    @ex.stage
    def part0(rnd):
       return rnd.randint(10)

    @ex.stage
    def part1(X, alpha, beta, logger):
       X -= alpha
       X *= beta
       logger.info("multiplied by %f and added %f", alpha, beta)
       return X

    @main
    def mainFunction():
       # this is the main method, here we put everything together
       X = part0() # note that we do not need to pass rnd
       X = part1(X) # and no alpha, beta, and logger


So we have to create an experiment and decorate all of our functions.
But what do we get for this?

* automatic option passing (alpha, beta)
* a logger
* a random number generator that is seeded by the experiment
* automatic caching of intermediate results

Magic Arguments
===============
The experiment can automatically pass options to it's stages. This helps to
change many parameters of your experiment without having to pass them around
manually. This feature can also be used to easily try different sets of options
or do whole option-sweeps automatically. There are also two special arguments
called rnd, and logger that the experiment generates.
But lets see an simple example first.

Simple example
--------------
If you call a stage you can leave some of the parameters unfilled, and the
experiment will try to fill them using it's own options dictionary::

    from mlizard.experiment import createExperiment
    ex = createExperiment()

    @ex.stage
    def foo(some_option):
        print some_option

    foo()    # TypeError: foo() is missing value(s) for ['some_option']
    ex.options["some_option"] = 5
    foo()    # will print 5
    foo(7)   # will print 7

This will run just fine and print "5" because that is the value of "some_option"
in the experiments options. Note however, that those options will typically come
from a config file, or config string.

Argument Priority
-----------------
The experiment will resolve conflicting arguments according to the
following priority:

#. positional and keyword arguments passed by the caller
#. options from the experiment
#. default-values

This is illustrated by the following example::

    @ex.stage
    def foo(a, b, c, d=400, e=500):
        print a, b, c, d, e

    ex.options = dict(a=10, b=20, c=30, d=40)
    foo(1, c=3) # prints 1, 20, 3, 40, 500

Special arguments
-----------------
The experiment also provides two special arguments called *logger* and *rnd*.

The *logger* helps you with two things: first it can be used to print out some
messages that get logged as you'd expect. Secondly it can be used to report some
intermediate results such that you can use them for live-plots.
(See section Logger)

The second one (*rnd*) is a numpy RandomState object, that you can use to
generate random data. The important fact about this is, that if you provide a
seed to the experiment then all rnd objects will be deterministically seeded.
This means you can easily reproduce an experiment run even though it depended on
randomness.


Roadmap
========
* easy option sweeps
* report file
* online results view
* database of runs/options/results
* git integration (track version of code for every result)




