#!/usr/bin/python
# coding=utf-8
# This file is part of the MLizard library published under the GPL3 license.
# Copyright (C) 2012  Klaus Greff
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division, print_function, unicode_literals

import numpy as np

from helpers import assert_not_equal, assert_true, assert_equal
from ..caches import sshash

def test_sshash_distinct_int_hashes():
    assert_not_equal(sshash(1), sshash(2))
    assert_not_equal(sshash(-1), sshash(1))
    assert_not_equal(sshash(0), sshash(1))
    assert_not_equal(sshash(1000), sshash(1001))

def test_sshash_distinct_float_hashes():
    assert_not_equal(sshash(1.), sshash(2.))
    assert_not_equal(sshash(-1.), sshash(1.))
    assert_not_equal(sshash(0.), sshash(1.))
    assert_not_equal(sshash(1000.), sshash(1001.))
    assert_not_equal(sshash(.0001), sshash(0.))

def test_sshash_int_and_float_matches():
    assert_equal(sshash(1.), sshash(1))
    assert_equal(sshash(-1.), sshash(-1))
    assert_equal(sshash(16.), sshash(16))
    assert_equal(sshash(10000.), sshash(10000))

def test_sshash_returns_int():
    for o in [0, 1.0, 15L, "foo", (1,2,3), None, [1, 2, 3], {'a' : 3, 'b' : 5}]:
        assert_equal(type(sshash(o)), int )

def test_sshash_equal_lists_equal_results():
    a = [1, 2, 3]
    b = [1, 2, 3]
    assert_not_equal(id(a), id(b))
    assert_equal(sshash(a), sshash(b))

def test_sshash_different_lists_different_results():
    a = [1, 2, 3]
    b = [1, 2, 4]
    assert_not_equal(sshash(a), sshash(b))

def test_sshash_equal_dicts_equal_results():
    a = {'a':1, 'b':2, 'c':3}
    b = {'a':1, 'b':2, 'c':3}
    assert_not_equal(id(a), id(b))
    assert_equal(sshash(a), sshash(b))

def test_sshash_different_dicts_different_results():
    a = {'a':1, 'b':2, 'c':3}
    b = {'a':1, 'b':7, 'c':3}
    assert_not_equal(sshash(a), sshash(b))

class foo(object):
    def __init__(self, a):
        self.a = a

def test_sshash_equal_user_defined_types_equal_results():
    f1 = foo(5)
    f2 = foo(5)
    assert_equal(sshash(f1), sshash(f2))

def test_sshash_different_user_defined_types_different_results():
    f1 = foo(5)
    f2 = foo(7)
    assert_not_equal(sshash(f1), sshash(f2))

def test_sshash_equal_nparrays_equal_results():
    a = np.arange(12).reshape(3,4)
    b = np.arange(12).reshape(3,4)
    assert_equal(sshash(a), sshash(b))

def test_sshash_different_nparrays_different_results():
    a = np.arange(12).reshape(3,4)
    b = np.arange(1, 13).reshape(3,4)
    assert_not_equal(sshash(a), sshash(b))

def test_sshash_different_shape_nparrays_different_results():
    a = np.arange(12).reshape(3,4)
    b = np.arange(12).reshape(4,3)
    assert_not_equal(sshash(a), sshash(b))

def test_sshash_different_type_nparrays_different_results():
    a = np.arange(12, dtype=np.uint8).reshape(3,4)
    b = np.arange(12, dtype=np.uint16).reshape(3,4)
    assert_not_equal(sshash(a), sshash(b))

class bar(object):
    def __hash__(self):
        return 27

def test_sshash_uses_hash_method():
    f = bar()
    assert_equal(sshash(f), 27)