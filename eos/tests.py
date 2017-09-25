#!/usr/bin/env python3
#   Eos - Verifiable elections
#   Copyright © 2017  RunasSudo (Yingtong Li)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

from unittest import *

from eos.core.bigint import *
from eos.core.bitstring import *
from eos.core.objects import *

import importlib
import os
import types

test_suite = TestSuite()

# All the TestCase's we dynamically generate inherit from this class
class BaseTestCase(TestCase):
	@classmethod
	def setUpClass(cls):
		cls.impl.setUpClass()
	
	@classmethod
	def add_method(cls, method):
		def call_method(self, *args):
			cls.impl.impl = self
			func = getattr(cls.impl, method)
			return func(*args)
		setattr(cls, method, call_method)

# Test discovery
import eos.core.tests
for dirpath, dirnames, filenames in os.walk('eos'):
	if dirpath == 'eos':
		# Skip this file
		continue
	if 'tests.py' in filenames:
		module = importlib.import_module(dirpath.replace('/', '.') + '.tests')
		for name in dir(module):
			obj = getattr(module, name)
			if isinstance(obj, type):
				if issubclass(obj, eos.core.tests.EosTestCase):
					cls = type(name + 'Impl', (BaseTestCase,), {'impl': obj()})
					for method in dir(cls.impl):
						if isinstance(getattr(cls.impl, method), types.MethodType) and not hasattr(cls, method):
							cls.add_method(method)
							if method.startswith('test_'):
								test_case = cls(method)
								test_suite.addTest(test_case)

TextTestRunner(verbosity=3).run(test_suite)
