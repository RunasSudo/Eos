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

from eos.core.tests import *

from eos.core.bigint import *
from eos.psgjjr.bitstream import *
from eos.psgjjr.crypto import *

class EGTestCase(EosTestCase):
	def test_eg(self):
		pt = DEFAULT_GROUP.random_element()
		sk = EGPrivateKey.generate()
		ct = sk.public_key.encrypt(pt)
		m = sk.decrypt(ct)
		self.assertEqualJSON(pt, m)

class BitStreamTestCase(EosTestCase):
	def test_bitstream(self):
		bs = BitStream(BigInt('100101011011', 2))
		self.assertEqual(bs.read(4), 0b1001)
		self.assertEqual(bs.read(4), 0b0101)
		self.assertEqual(bs.read(4), 0b1011)
		bs = BitStream()
		bs.write(BigInt('100101011011', 2))
		bs.seek(0)
		self.assertEqual(bs.read(4), 0b1001)
		self.assertEqual(bs.read(4), 0b0101)
		self.assertEqual(bs.read(4), 0b1011)
		bs.seek(4)
		bs.write(BigInt('11', 2))
		bs.seek(0)
		self.assertEqual(bs.read(4), 0b1001)
		self.assertEqual(bs.read(4), 0b1101)
		self.assertEqual(bs.read(4), 0b0110)
		self.assertEqual(bs.read(2), 0b11)
	
	def test_bitstream_map(self):
		bs = BitStream(BigInt('100101011011', 2))
		result = bs.map(lambda x: x, 4)
		expect = [0b1001, 0b0101, 0b1011]
		for i in range(len(expect)):
			self.assertEqual(result[i], expect[i])
	
	def test_strings(self):
		bs = BitStream()
		bs.write_string('Hello World!')
		bs.seek(0)
		self.assertEqual(bs.read(32), len('Hello World!'))
		bs.seek(0)
		self.assertEqual(bs.read_string(), 'Hello World!')

class BlockEGTestCase(EosTestCase):
	@classmethod
	def setUpClass(cls):
		class Person(TopLevelObject):
			name = StringField()
			address = StringField(default=None)
			def say_hi(self):
				return 'Hello! My name is ' + self.name
		
		cls.Person = Person
		
		#cls.test_group = CyclicGroup(p=BigInt('11'), g=BigInt('2'))
		cls.test_group = CyclicGroup(p=BigInt('283'), g=BigInt('60'))
		cls.sk = EGPrivateKey.generate(cls.test_group)
	
	def test_basic(self):
		pt = BigInt('11010010011111010100101', 2)
		ct = BitStream(pt).multiple_of(self.test_group.p.nbits() - 1).map(self.sk.public_key.encrypt, self.test_group.p.nbits() - 1)
		for i in range(len(ct)):
			self.assertTrue(ct[i].gamma < self.test_group.p)
			self.assertTrue(ct[i].delta < self.test_group.p)
		m = BitStream.unmap(ct, self.sk.decrypt, self.test_group.p.nbits() - 1).read()
		self.assertEqualJSON(pt, m)
	
	def test_object(self):
		obj = self.Person(name='John Smith')
		pt = EosObject.to_json(EosObject.serialise_and_wrap(obj))
		bs = BitStream()
		bs.write_string(pt)
		bs.multiple_of(self.test_group.p.nbits() - 1, True)
		ct = bs.map(self.sk.public_key.encrypt, self.test_group.p.nbits() - 1)
		bs2 = BitStream.unmap(ct, self.sk.decrypt, self.test_group.p.nbits() - 1)
		m = bs2.read_string()
		obj2 = EosObject.deserialise_and_unwrap(EosObject.from_json(m))
		self.assertEqualJSON(obj, obj2)
