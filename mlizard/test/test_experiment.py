#!/usr/bin/python
# coding=utf-8
# This file is part of the MLizard library published under the GPL3 license.
# Copyright (C) 2012  Klaus Greff
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import division, print_function, unicode_literals

import logging
from tempfile import NamedTemporaryFile

from helpers import *
from ..factory import createExperiment, create_basic_Experiment

# don't gather logging spam
logging.disable(logging.CRITICAL)

def test_Experiment_constructor_works():
    ex1 = create_basic_Experiment()

def test_Experiment_provides_stage_decorator():
    ex1 = create_basic_Experiment()

    @ex1.stage
    def foo(): pass

    assert_true(hasattr(foo, '__call__'))

def test_stage_decorator_retains_docstring():
    ex1 = create_basic_Experiment()

    @ex1.stage
    def foo():
        """
        Test-Docstring
        """
        pass

    assert_equal(foo.__doc__.strip(), "Test-Docstring")

def test_stage_decorator_retains_function_name():
    ex1 = create_basic_Experiment()

    @ex1.stage
    def foo(): pass

    assert_equal(foo.func_name, "foo")

def test_Experiment_keeps_track_of_stages():
    ex1 = create_basic_Experiment()

    @ex1.stage
    def foo(): pass

    @ex1.stage
    def bar(): pass

    @ex1.stage
    def baz(): pass

    assert_equal(ex1.stages["foo"], foo)
    assert_equal(ex1.stages["bar"], bar)
    assert_equal(ex1.stages["baz"], baz)


def test_stage_executes_function():
    ex1 = create_basic_Experiment()
    a = []

    @ex1.stage
    def foo():
        a.append("executed")

    foo()
    assert_equal(a, ["executed"])

def test_Experiment_stores_options():
    ex1 = create_basic_Experiment()
    ex1.options["alpha"] = 0.7
    assert_equal(ex1.options["alpha"], 0.7)

def test_fill_args_applies_options():
    ex1 = create_basic_Experiment()
    ex1.options["alpha"] = 0.7
    ex1.options["beta"] = 1.2

    @ex1.stage
    def foo(alpha, beta):
        return alpha, beta

    #noinspection PyArgumentList
    assert_equal(foo(), (0.7, 1.2))

def test_stage_overrides_default_with_options():
    ex1 = create_basic_Experiment()
    ex1.options["alpha"] = 0.7
    ex1.options["beta"] = 1.2

    @ex1.stage
    def foo(alpha=0, beta=0):
        return alpha, beta

    assert_equal(foo(), (0.7, 1.2))

def test_stage_keeps_explicit_arguments():
    ex1 = create_basic_Experiment()
    ex1.options["alpha"] = 0.7
    ex1.options["beta"] = 1.2

    @ex1.stage
    def foo(alpha, beta):
        return alpha, beta

    assert_equal(foo(0, beta=0), (0, 0))

@raises(TypeError)
def test_stage_with_unexpected_kwarg_raises_TypeError():
    ex1 = create_basic_Experiment()

    @ex1.stage
    def foo(): pass

    #noinspection PyArgumentList
    foo(unexpected=1)

@raises(TypeError)
def test_stage_with_duplicate_arguments_raises_TypeError():
    ex1 = create_basic_Experiment()

    @ex1.stage
    def foo(a): pass

    #noinspection PyArgumentList
    foo(2, a=1)

@raises(TypeError)
def test_stage_with_missing_arguments_raises_TypeError():
    ex1 = create_basic_Experiment()
    ex1.options["b"]=1
    @ex1.stage
    def foo(a, b, c, d=5): pass

    #noinspection PyArgumentList
    foo(1)

def test_experiment_reads_options_from_file():
    with NamedTemporaryFile() as f:
        f.write("""
        foo=1
        bar=7.5
        baz='abc'
        complex=[1, 2.0, 'a', [1, 2]]
        d={'a' : 1, 'b' : 2}
        """)
        f.flush()
        ex1 = createExperiment(config_file=f.name)
        assert_true("foo" in ex1.options)
        assert_equal(ex1.options['foo'], 1)
        assert_true("bar" in ex1.options)
        assert_equal(ex1.options['bar'], 7.5)
        assert_true("baz" in ex1.options)
        assert_equal(ex1.options['baz'], "abc")
        assert_true("complex" in ex1.options)
        assert_equal(ex1.options['complex'], [1, 2.0, 'a', [1, 2]])
        assert_true("d" in ex1.options)
        assert_equal(ex1.options['d'], {'a' : 1, 'b' : 2})

@nottest
def test_experiment_reads_seed_from_file():
    with NamedTemporaryFile() as f:
        f.write("""
        seed=54321
        """)
        f.flush()
        ex1 = createExperiment(config_file=f.name)
        assert_equal(ex1.seed, 54321)


def test_fill_args_seeds_deterministic():
    ex1 = create_basic_Experiment(seed=12345)
    @ex1.stage
    def foo(rnd):
        return rnd.randint(10000)
    r1 = foo()

    ex1 = create_basic_Experiment(seed=12345)
    @ex1.stage
    def foo(rnd):
        return rnd.randint(10000)
    r2 = foo()

    assert_equal(r1, r2)

def test_repeated_fill_args_are_seeded_differently():
    ex1 = create_basic_Experiment(seed=12345)
    @ex1.stage
    def foo(rnd):
        return rnd.randint(10000)

    r1 = foo()
    r2 = foo()

    assert_not_equal(r1, r2)

