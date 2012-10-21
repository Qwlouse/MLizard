#!/usr/bin/python
# coding=utf-8
from __future__ import division, print_function, unicode_literals

import pickle
import shelve

def sshash(obj):
    try:
        return hash(obj)
    except TypeError:
        return hash(pickle.dumps(obj))


class ShelveCache(object):
    def __init__(self, filename):
        self.shelve = shelve.open(filename)

    def transform_key(self, key):
        return hex(sshash(key))

    def __getitem__(self, item):
        return self.shelve[self.transform_key(item)]

    def __setitem__(self, key, value):
        self.shelve[self.transform_key(key)] = value

    def __delitem__(self, key):
        self.shelve.__delitem__(self.transform_key(key))

    def __del__(self):
        self.shelve.sync()
        self.shelve.close()

    def sync(self):
        self.shelve.sync()

class CacheStub(object):
    def __getitem__(self, item):
        raise KeyError("Key not Found.")

    def __setitem__(self, key, value):
        pass

    def __delitem__(self, key):
        pass

    def sync(self):
        pass
