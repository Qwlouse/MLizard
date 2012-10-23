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
    # we import the experiment factory
    from mlizard.experiment import createExperiment

    # at the beginning of the file we create an experiment
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
- automatic option passing (alpha, beta)
- a logger
- a random number generator that is seeded by the experiment
- automatic caching of intermediate results

More to come (Roadmap):
- easy option sweeps
- report file
- online results view
- database of runs/options/results
- git integration (track version of code for every result)




