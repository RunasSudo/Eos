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
from eos.psr.bitstream import *
from eos.psr.crypto import *

class EGTestCase(EosTestCase):
	def test_eg(self):
		pt = DEFAULT_GROUP.random_element()
		sk = EGPrivateKey.generate()
		ct = sk.public_key.encrypt(pt)
		m = sk.decrypt(ct)
		self.assertEqualJSON(pt, m)

class SEGTestCase(EosTestCase):
	def test_eg(self):
		pt = DEFAULT_GROUP.random_element()
		sk = SEGPrivateKey.generate()
		ct = sk.public_key.encrypt(pt)
		self.assertTrue(ct.is_signature_valid())
		m = sk.decrypt(ct)
		self.assertEqualJSON(pt, m)
		
		ct2, _ = ct.reencrypt()
		m2 = sk.decrypt(ct2)
		self.assertEqualJSON(pt, m2)

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

class MixnetTestCase(EosTestCase):
	@py_only
	def test_mixnet(self):
		# Generate key
		sk = SEGPrivateKey.generate()
		
		# Generate plaintexts
		pts = []
		for i in range(10):
			pts.append(sk.public_key.group.random_element())
		
		# Encrypt plaintexts
		answers = []
		for i in range(len(pts)):
			bs = BitStream(pts[i])
			bs.multiple_of(sk.public_key.group.p.nbits() - 1)
			ct = bs.map(sk.public_key.encrypt, sk.public_key.group.p.nbits() - 1)
			answers.append(BlockEncryptedAnswer(blocks=ct))
		
		# Set up mixnet
		mixnet = RPCMixnet()
		
		# Mix answers
		shuffled_answers, commitments_left, commitments_right = mixnet.shuffle(answers)
		
		# Decrypt shuffle
		msgs = []
		for i in range(len(shuffled_answers)):
			bs = BitStream.unmap(shuffled_answers[i].blocks, sk.decrypt, sk.public_key.group.p.nbits() - 1)
			m = bs.read()
			msgs.append(m)
		
		# Check decryption
		self.assertEqual(set(int(x) for x in pts), set(int(x) for x in msgs))
		
		# Check commitments
		def verify_shuffle(idx_left, idx_right, reencs):
			claimed_blocks = shuffled_answers[idx_right].blocks
			for j in range(len(answers[idx_left].blocks)):
				reencrypted_block, _ = answers[idx_left].blocks[j].reencrypt(reencs[j])
				self.assertEqual(claimed_blocks[j].gamma, reencrypted_block.gamma)
				self.assertEqual(claimed_blocks[j].delta, reencrypted_block.delta)
		
		for i in range(len(pts)):
			# Left
			perm, reencs, rand = mixnet.challenge(i, True)
			val_json = [perm, [str(x) for x in reencs], str(rand)]
			self.assertEqual(commitments_left[i], EosObject.to_sha256(EosObject.to_json(val_json))[0])
			verify_shuffle(i, perm, reencs)
			
			# Right
			perm, reencs, rand = mixnet.challenge(i, False)
			val_json = [perm, [str(x) for x in reencs], str(rand)]
			self.assertEqual(commitments_right[i], EosObject.to_sha256(EosObject.to_json(val_json))[0])
			verify_shuffle(perm, i, reencs)
