#!/usr/bin/python
# coding: utf-8
from __future__ import division, unicode_literals, print_function

from nose.tools import istest, nottest, with_setup
from nose.tools import assert_true as _assert_true
from nose.tools import assert_not_equal as _assert_not_equal
from nose.tools import raises
from numpy.testing import assert_almost_equal, assert_equal, assert_allclose
from numpy.testing import assert_array_less as assert_less

def assert_true(expr, msg=None):
    _assert_true(expr, msg)

def assert_not_equal(first, second, msg=None):
    _assert_not_equal(first, second, msg)

# Use the same flag as unittest itself to prevent descent into these functions:
__unittest = 1
