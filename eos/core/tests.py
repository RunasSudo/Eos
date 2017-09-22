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

from unittest import TestCase

from eos.core.objects import *

class PyTestCase(TestCase):
	@classmethod
	def setUpClass(cls):
		class Person(TopLevelObject):
			name = StringField()
			address = StringField(default=None)
			def say_hi(self):
				return 'Hello! My name is ' + self.name
		
		cls.Person = Person
	
	def test_basic_py(self):
		person1 = self.Person(name='John', address='Address 1')
		person2 = self.Person(name='James', address='Address 2')
		
		self.assertEqual(person1.address, 'Address 1')
		self.assertEqual(person2.address, 'Address 2')
		self.assertEqual(person1.say_hi(), 'Hello! My name is John')
		self.assertEqual(person2.say_hi(), 'Hello! My name is James')
	
	def test_serialise_py(self):
		person1 = self.Person(name='John', address='Address 1')
		expect1 = {'name': 'John', 'address': 'Address 1'}
		
		self.assertEqual(person1.serialise(), expect1)
		self.assertEqual(EosObject.serialise_and_wrap(person1, self.Person), expect1)
		self.assertEqual(EosObject.serialise_and_wrap(person1), {'type': 'eos.core.tests.PyTestCase.setUpClass.<locals>.Person', 'value': expect1})
