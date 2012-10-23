#!/usr/bin/python
# coding=utf-8
# This file is part of the MLizard library published under the GPL3 license.
# Copyright (C) 2012  Klaus Greff
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import division, print_function, unicode_literals

import numpy as np
from tempfile import NamedTemporaryFile

from mlizard.caches import ShelveCache
from helpers import *

def foonction():
    pass

class Bar(object):
    def __init__(self, a):
        self.a = a

    def __eq__(self, other):
        return self.a == other.a

    def __ne__(self, other):
        return not self.__eq__(other)

TEST_OBJECTS = [1, 1234567890L, 0.5, u'unicode', b"bytestring",
                (1,2), ['a', 5], {'a' : 1}, np.array([1, 2]),
                foonction, Bar, Bar(17)]
@nottest
def test_ShelveCache_uses_arbitrary_keys():
    with NamedTemporaryFile() as f:
        cache = ShelveCache(f.name)
        key_value_pairs = zip(TEST_OBJECTS, range(len(TEST_OBJECTS)))
        for k, v in key_value_pairs:
            cache[k] = v

        for k,v in key_value_pairs:
            assert_equal(cache[k], v)

@nottest
def test_ShelveCache_stores_arbitrary_values():
    with NamedTemporaryFile() as f:
        cache = ShelveCache(f.name)
        key_value_pairs = zip(range(len(TEST_OBJECTS)), TEST_OBJECTS)
        for k, v in key_value_pairs:
            cache[k] = v

        for k,v in key_value_pairs:
            assert_equal(cache[k], v)