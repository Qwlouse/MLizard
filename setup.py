#!/usr/bin/python
# coding=utf-8
# This file is part of the MLizard library published under the GPL3 license.
# Copyright (C) 2012  Klaus Greff
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from distutils.core import setup
import mlizard

setup(
    name='MLizard',
    version=mlizard.__version__,
    author='Klaus Greff',
    author_email='klaus.greff@gmx.net',
    packages=['mlizard', 'mlizard.test'],
    scripts=[],
    url='http://pypi.python.org/pypi/MLizard/',
    license='LICENSE.txt',
    description='Machine Learning workflow automatization',
    long_description=open('README.rst').read(),
    install_requires=[
        "numpy >= 1.6.1",
        "matplotlib >= 1.1.0",
        "configobj >= 4.7.2",
        "nose >= 1.1.2"
    ],
)
