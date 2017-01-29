#    Copyright © 2017  RunasSudo (Yingtong Li)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import eos_stjjr.crypto

#import django.test
import unittest

class CryptoTest(unittest.TestCase):
#class CryptoTest(django.test.TestCase):
	TARGET_BASIC = 3
	
	# HAC 4.24
	def miller_rabin_test(self, n, t=10):
		# Write n - 1 = 2^s r such that r is odd
		s = eos_stjjr.bigint.ZERO
		r = n - eos_stjjr.bigint.ONE
		while (r % eos_stjjr.bigint.TWO) == eos_stjjr.bigint.ZERO:
			r = r // eos_stjjr.bigint.TWO
			s += eos_stjjr.bigint.ONE
		
		# Pre-compute some parameters
		s_1 = s - eos_stjjr.bigint.ONE
		n_1 = n - eos_stjjr.bigint.ONE
		n_2 = n - eos_stjjr.bigint.TWO
		
		for i in range(0, t):
			a = eos_stjjr.bigint.noncrypto_random(eos_stjjr.bigint.TWO, n_2)
			y = pow(a, r, n)
			if y == eos_stjjr.bigint.ONE or y == n_1:
				continue
			j = eos_stjjr.bigint.ONE
			while j <= s_1 and y != n_1:
				y = pow(y, eos_stjjr.bigint.TWO, n)
				if y == eos_stjjr.bigint.ONE:
					return False
				j += eos_stjjr.bigint.ONE
			if y != n_1:
				return False
		
		return True
	
	def test_miller_rabin(self):
		self.assertTrue(self.miller_rabin_test(eos_stjjr.bigint.BigInt('179426549')))
		self.assertTrue(self.miller_rabin_test(eos_stjjr.bigint.BigInt('32416190071')))
		self.assertFalse(self.miller_rabin_test(eos_stjjr.bigint.BigInt('68909411'))) # 7927*8693
		self.assertFalse(self.miller_rabin_test(eos_stjjr.bigint.BigInt('77527349'))) # 8779*8831
	
	def test_group_random(self):
		group = eos_stjjr.crypto.CyclicGroup(p=eos_stjjr.bigint.BigInt('11'), g=eos_stjjr.bigint.TWO)
		
		noncrypto_random = eos_stjjr.bigint.noncrypto_random
		crypto_random = eos_stjjr.bigint.crypto_random
		def dummy(a, b):
			raise Exception('Wrong function called in test')
		
		# Check crypto_random
		eos_stjjr.bigint.crypto_random = dummy
		with self.assertRaisesRegex(Exception, 'Wrong function called in test'):
			group.random_element()
		with self.assertRaisesRegex(Exception, 'Wrong function called in test'):
			group.random_element(True)
		group.random_element(False)
		eos_stjjr.bigint.crypto_random = crypto_random
		
		# Check noncrypto_random
		eos_stjjr.bigint.noncrypto_random = dummy
		group.random_element()
		group.random_element(True)
		with self.assertRaisesRegex(Exception, 'Wrong function called in test'):
			group.random_element(False)
		eos_stjjr.bigint.noncrypto_random = noncrypto_random
		
		# Check range
		random_numbers = []
		for i in range(100):
			num = group.random_element(False)
			self.assertTrue(isinstance(num, eos_stjjr.bigint.BigInt))
			random_numbers.append(int(num))
		self.assertTrue(min(random_numbers) == 1)
		self.assertTrue(max(random_numbers) == 10)
	
	def test_default_group_params(self):
		self.assertTrue(self.miller_rabin_test(eos_stjjr.crypto.DEFAULT_GROUP.p))
		q = eos_stjjr.crypto.DEFAULT_GROUP.q
		self.assertEqual(eos_stjjr.crypto.DEFAULT_GROUP.p, q * eos_stjjr.bigint.TWO + eos_stjjr.bigint.ONE)
		self.assertTrue(self.miller_rabin_test(q))
	
	def generate_plaintext(self):
		return eos_stjjr.bigint.noncrypto_random(eos_stjjr.bigint.ONE, eos_stjjr.crypto.DEFAULT_GROUP.p - eos_stjjr.bigint.ONE)
	
	def test_cpseg(self):
		# s = a + c*r
		# s < p + (max 256-bit)*p
		# s < p*(max 256-bit + 1)
		MAX_SIGNATURE = eos_stjjr.bigint.BigInt('10000000000000000000000000000000000000000000000000000000000000000', 16) * eos_stjjr.crypto.DEFAULT_GROUP.p
		
		for i in range(CryptoTest.TARGET_BASIC):
			pt = self.generate_plaintext()
			#print('Round {} plaintext {}'.format(i, pt))
			sk = eos_stjjr.crypto.CPSEGPrivateKey.generate()
			ct = sk.public_key.encrypt(pt)
			
			# Check that the signature makes sense
			self.assertTrue(ct.s > eos_stjjr.bigint.ZERO)
			self.assertTrue(ct.s < MAX_SIGNATURE)
			
			m = sk.decrypt(ct)
			self.assertEqual(pt, m)
	
	def test_cpseg_replace(self):
		for i in range(CryptoTest.TARGET_BASIC):
			pt1 = self.generate_plaintext()
			pt2 = self.generate_plaintext()
			#print('Round {} plaintexts {} and {}'.format(i, pt1, pt2))
			sk = eos_stjjr.crypto.CPSEGPrivateKey.generate()
			ct1 = sk.public_key.encrypt(pt1)
			ct2 = sk.public_key.encrypt(pt2)
			ct = eos_stjjr.crypto.CPSEGCiphertext(public_key=ct1.public_key, R=ct2.R, Y=ct2.Y, A=ct1.A, s=ct1.s)
			with self.assertRaisesRegex(Exception, 'Signature is incorrect'):
				sk.decrypt(ct)
	
	def test_cpseg_homomorphic(self):
		for i in range(CryptoTest.TARGET_BASIC):
			pt = self.generate_plaintext()
			#print('Round {} plaintext {}'.format(i, pt))
			sk = eos_stjjr.crypto.CPSEGPrivateKey.generate()
			ct = sk.public_key.encrypt(pt)
			# ElGamal is multiplicatively homomorphic
			ct2 = eos_stjjr.crypto.CPSEGCiphertext(public_key=ct.public_key, R=pow(ct.R, eos_stjjr.bigint.TWO, sk.public_key.group.p), Y=pow(ct.Y, eos_stjjr.bigint.TWO, sk.public_key.group.p), A=ct.A, s=ct.s)
			with self.assertRaisesRegex(Exception, 'Signature is incorrect'):
				sk.decrypt(ct2)
	
	def test_cpseg_malformed(self):
		NEG_ONE = eos_stjjr.bigint.BigInt('-1')
		
		def test_attrib(sk, ct, attrib):
			ct2 = eos_stjjr.crypto.CPSEGCiphertext(public_key=ct.public_key, R=ct.R, Y=ct.Y, A=ct.A, s=ct.s)
			setattr(ct2, attrib, sk.public_key.group.p - eos_stjjr.bigint.ONE)
			with self.assertRaisesRegex(Exception, 'Signature is incorrect'):
				sk.decrypt(ct2)
			setattr(ct2, attrib, sk.public_key.group.p)
			with self.assertRaisesRegex(Exception, 'Ciphertext is malformed'):
				sk.decrypt(ct2)
			setattr(ct2, attrib, sk.public_key.group.p + eos_stjjr.bigint.ONE)
			with self.assertRaisesRegex(Exception, 'Ciphertext is malformed'):
				sk.decrypt(ct2)
			setattr(ct2, attrib, eos_stjjr.bigint.ONE)
			with self.assertRaisesRegex(Exception, 'Signature is incorrect'):
				sk.decrypt(ct2)
			setattr(ct2, attrib, eos_stjjr.bigint.ZERO)
			with self.assertRaisesRegex(Exception, 'Ciphertext is malformed'):
				sk.decrypt(ct2)
			setattr(ct2, attrib, NEG_ONE)
			with self.assertRaisesRegex(Exception, 'Ciphertext is malformed'):
				sk.decrypt(ct2)
		
		for i in range(CryptoTest.TARGET_BASIC):
			pt = self.generate_plaintext()
			sk = eos_stjjr.crypto.CPSEGPrivateKey.generate()
			ct = sk.public_key.encrypt(pt)
			test_attrib(sk, ct, 'R')
			test_attrib(sk, ct, 'Y')
			test_attrib(sk, ct, 'A')
