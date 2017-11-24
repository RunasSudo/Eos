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

import execjs

import importlib
import os
import sys
import types

test_suite = TestSuite()

# All the TestCase's we dynamically generate inherit from these classes
class BasePyTestCase(TestCase):
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

class BaseJSTestCase(TestCase):
	@classmethod
	def setUpClass(cls):
		with open('eos/__javascript__/eos.js_tests.js', 'r') as f:
			code = f.read()
		cls.ctx = execjs.get().compile('var window={},navigator={};' + code + 'var test=window.eosjs_tests.' + cls.module + '.__all__.' + cls.name + '();test.setUpClass();')
	
	@classmethod
	def add_method(cls, method):
		def call_method(self, *args):
			# TODO: args
			try:
				return cls.ctx.eval('test.' + method + '()')
			except execjs._exceptions.ProcessExitedWithNonZeroStatus as ex:
				import traceback
				traceback.print_exc()
				print(ex.stderr)
				self.fail()
		setattr(cls, method, call_method)

# Test discovery
def run_tests(prefix=None, lang=None):
	import eos.core.tests
	for dirpath, dirnames, filenames in os.walk('eos'):
		if dirpath == 'eos':
			# Skip this file
			continue
		if 'tests.py' in filenames:
			module_name = dirpath.replace('/', '.') + '.tests'
			module = importlib.import_module(module_name)
			for name in dir(module):
				obj = getattr(module, name)
				if isinstance(obj, type):
					if issubclass(obj, eos.core.tests.EosTestCase):
						if obj.__module__ != module_name:
							continue
						if prefix is not None and not obj.__module__.startswith(prefix):
							continue
						
						impl = obj()
						cls_py = type(name + 'ImplPy', (BasePyTestCase,), {'__module__': module_name, 'impl': impl})
						cls_js = type(name + 'ImplJS', (BaseJSTestCase,), {'__module__': module_name, 'module': module_name, 'name': name})
						for method in dir(impl):
							method_val = getattr(impl, method)
							if isinstance(method_val, types.MethodType) and not hasattr(cls_py, method):
								# Python
								if not (lang is not None and lang == 'js') and not getattr(method_val, '_js_only', False):
									cls_py.add_method(method)
									if method.startswith('test_'):
										test_case = cls_py(method)
										test_suite.addTest(test_case)
								
								# Javascript
								if not (lang is not None and lang == 'py') and not getattr(method_val, '_py_only', False):
									if method.startswith('test_'):
										cls_js.add_method(method)
										test_case = cls_js(method)
										test_suite.addTest(test_case)
	
	TextTestRunner(verbosity=3, failfast=True).run(test_suite)

if __name__ == '__main__':
	run_tests(*sys.argv[1:])
