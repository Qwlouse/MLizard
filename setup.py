#!/usr/bin/python
# coding=utf-8
# This file is part of the MLizard library published under the GPL3 license.
# Copyright (C) 2012  Klaus Greff
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from distutils.core import setup

setup(
    name='MLizard',
    version='0.1.0',
    author='Klaus Greff',
    author_email='klaus.greff@gmx.net',
    packages=['mlizard', 'mlizard.test'],
    scripts=[],
#    url='http://pypi.python.org/pypi/TowelStuff/',
    license='LICENSE.txt',
    description='Machine Learning workflow automatization',
    long_description=open('README').read(),
    install_requires=[
        "numpy >= 1.6.1",
        "matplotlib >= 1.1.0",
        "configobj >= 4.7.2",
        "nose >= 1.2.1"
    ],
)
