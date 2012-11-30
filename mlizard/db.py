#!/usr/bin/python
# coding=utf-8
# This file is part of the MLizard library published under the GPL3 license.
# Copyright (C) 2012  Klaus Greff
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
docstring
"""
from __future__ import division, print_function, unicode_literals

class StageDBInterface(object):
    def __init__(self, db):
        self.db = db
        self.db_entry = None

    def save(self, stage_entry):
        assert self.db_entry is not None
        if not stage_entry in self.db_entry['stages']:
            self.db_entry['stages'].append(stage_entry)
        if self.db :
            self.db.save(self.db_entry)

class DummyDB(object):
    def __init__(self):
        pass

    def save(self, a):
        pass