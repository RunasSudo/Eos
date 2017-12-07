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

from eos.core.bigint import *
from eos.core.objects import *
from eos.core.hashing import *
from eos.core.tasks import *

# Common library things
# ===================

class EosTestCase:
	@classmethod
	def setUpClass(cls):
		pass
	
	@classmethod
	def db_connect_and_reset(cls):
		db_connect('test')
		dbinfo.provider.reset_db()
	
	def assertTrue(self, a):
		if is_python:
			self.impl.assertTrue(a)
		else:
			if not a:
				raise Error('Assertion failed: ' + str(a) + ' not True')
	
	def assertFalse(self, a):
		if is_python:
			self.impl.assertFalse(a)
		else:
			if not a:
				raise Error('Assertion failed: ' + str(a) + ' not False')
	
	def assertEqual(self, a, b):
		if is_python:
			self.impl.assertEqual(a, b)
		else:
			if a is None:
				if b is not None:
					raise Error('Assertion failed: ' + str(a) + ' != ' + str(b))
			else:
				if a != b:
					raise Error('Assertion failed: ' + str(a) + ' != ' + str(b))
	
	def assertEqualJSON(self, a, b):
		if isinstance(a, EosObject):
			a = EosObject.serialise_and_wrap(a)
		if isinstance(b, EosObject):
			b = EosObject.serialise_and_wrap(b)
		self.assertEqual(EosObject.to_json(a), EosObject.to_json(b))

def py_only(func):
	func._py_only = True
	return func
def js_only(func):
	func._js_only = True
	return func

# eos.core tests
# ==============

class ObjectTestCase(EosTestCase):
	@classmethod
	def setUpClass(cls):
		class Person(TopLevelObject):
			name = StringField()
			address = StringField(default='Default address')
			def say_hi(self):
				return 'Hello! My name is ' + self.name
		
		cls.Person = Person
	
	def test_basic(self):
		person1 = self.Person(name='John', address='Address 1')
		person2 = self.Person(name='James')
		
		self.assertEqual(person1.address, 'Address 1')
		self.assertEqual(person2.address, 'Default address')
		self.assertEqual(person1.say_hi(), 'Hello! My name is John')
		self.assertEqual(person2.say_hi(), 'Hello! My name is James')
	
	def test_serialise(self):
		person1 = self.Person(name='John', address='Address 1')
		expect1 = {'_ver': '0.1', 'name': 'John', 'address': 'Address 1'}
		#expect1a = {'type': 'eos.core.tests.ObjectTestCase.setUpClass.<locals>.Person', 'value': expect1}
		expect1a = {'type': 'eos.core.tests.Person', 'value': expect1}
		
		self.assertEqualJSON(person1.serialise(), expect1)
		self.assertEqualJSON(EosObject.serialise_and_wrap(person1, self.Person), expect1)
		self.assertEqualJSON(EosObject.serialise_and_wrap(person1), expect1a)
		
		#self.assertEqual(EosObject.deserialise_and_unwrap(expect1a), person1)
		self.assertEqualJSON(EosObject.deserialise_and_unwrap(expect1a).serialise(), person1.serialise())

class HashTestCase(EosTestCase):
	def test_hash(self):
		self.assertEqual(SHA256().update_text('Hello World!').hash_as_b64(), 'f4OxZX/x/FO5LcGBSKHWXfwtSx+j1ncoSt3SABJtkGk=')

class BigIntTestCase(EosTestCase):
	def test_basic(self):
		bigint1 = BigInt(5)
		bigint2 = BigInt('A', 16)
		bigint3 = BigInt('15')
		
		self.assertEqual(bigint1, 5)
		self.assertEqual(bigint2, 10)
		self.assertEqual(bigint3, 15)
		
		self.assertEqual(bigint1 + bigint2, 15)
		self.assertEqual(bigint3 - bigint2, bigint1)
		self.assertEqual(pow(bigint1, bigint2), 5**10)
		self.assertEqual(pow(bigint1, bigint2, bigint3), (5**10)%15)
		self.assertEqual(pow(bigint1, 10, 15), (5**10)%15)

class TaskTestCase(EosTestCase):
	@classmethod
	def setUpClass(cls):
		cls.db_connect_and_reset()
	
	def test_normal(self):
		class TaskNormal(Task):
			result = StringField()
			def _run(self):
				self.messages.append('Hello World')
				self.result = 'Success'
		
		task = TaskNormal(run_strategy=DirectRunStrategy())
		task.save()
		task.run()
		
		self.assertEqual(task.status, Task.Status.COMPLETE)
		self.assertEqual(len(task.messages), 1)
		self.assertEqual(task.messages[0], 'Hello World')
		self.assertEqual(task.result, 'Success')
	
	def test_error(self):
		class TaskError(Task):
			def _run(self):
				raise Exception('Test exception')
		
		task = TaskError(run_strategy=DirectRunStrategy())
		task.save()
		task.run()
		
		self.assertEqual(task.status, Task.Status.FAILED)
		self.assertEqual(len(task.messages), 1)
		self.assertTrue('Test exception' in task.messages[0])
