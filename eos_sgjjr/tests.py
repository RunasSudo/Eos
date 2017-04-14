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

import eos_sgjjr.crypto

#import django.test
import unittest

class CryptoTest(unittest.TestCase):
#class CryptoTest(django.test.TestCase):
	TARGET_BASIC = 3
	
	# HAC 4.24
	def miller_rabin_test(self, n, t=10):
		# Write n - 1 = 2^s r such that r is odd
		s = eos_sgjjr.bigint.ZERO
		r = n - eos_sgjjr.bigint.ONE
		while (r % eos_sgjjr.bigint.TWO) == eos_sgjjr.bigint.ZERO:
			r = r // eos_sgjjr.bigint.TWO
			s += eos_sgjjr.bigint.ONE
		
		# Pre-compute some parameters
		s_1 = s - eos_sgjjr.bigint.ONE
		n_1 = n - eos_sgjjr.bigint.ONE
		n_2 = n - eos_sgjjr.bigint.TWO
		
		for i in range(0, t):
			a = eos_sgjjr.bigint.noncrypto_random(eos_sgjjr.bigint.TWO, n_2)
			y = pow(a, r, n)
			if y == eos_sgjjr.bigint.ONE or y == n_1:
				continue
			j = eos_sgjjr.bigint.ONE
			while j <= s_1 and y != n_1:
				y = pow(y, eos_sgjjr.bigint.TWO, n)
				if y == eos_sgjjr.bigint.ONE:
					return False
				j += eos_sgjjr.bigint.ONE
			if y != n_1:
				return False
		
		return True
	
	def test_miller_rabin(self):
		self.assertTrue(self.miller_rabin_test(eos_sgjjr.bigint.BigInt('179426549')))
		self.assertTrue(self.miller_rabin_test(eos_sgjjr.bigint.BigInt('32416190071')))
		self.assertFalse(self.miller_rabin_test(eos_sgjjr.bigint.BigInt('68909411'))) # 7927*8693
		self.assertFalse(self.miller_rabin_test(eos_sgjjr.bigint.BigInt('77527349'))) # 8779*8831
	
	def test_group_random(self):
		group = eos_sgjjr.crypto.CyclicGroup(p=eos_sgjjr.bigint.BigInt('11'), g=eos_sgjjr.bigint.TWO)
		
		noncrypto_random = eos_sgjjr.bigint.noncrypto_random
		crypto_random = eos_sgjjr.bigint.crypto_random
		def dummy(a, b):
			raise Exception('Wrong function called in test')
		
		# Check crypto_random
		eos_sgjjr.bigint.crypto_random = dummy
		with self.assertRaisesRegex(Exception, 'Wrong function called in test'):
			group.random_element()
		with self.assertRaisesRegex(Exception, 'Wrong function called in test'):
			group.random_element(True)
		group.random_element(False)
		eos_sgjjr.bigint.crypto_random = crypto_random
		
		# Check noncrypto_random
		eos_sgjjr.bigint.noncrypto_random = dummy
		group.random_element()
		group.random_element(True)
		with self.assertRaisesRegex(Exception, 'Wrong function called in test'):
			group.random_element(False)
		eos_sgjjr.bigint.noncrypto_random = noncrypto_random
		
		# Check range
		random_numbers = []
		for i in range(100):
			num = group.random_element(False)
			self.assertTrue(isinstance(num, eos_sgjjr.bigint.BigInt))
			random_numbers.append(int(num))
		self.assertTrue(min(random_numbers) == 1)
		self.assertTrue(max(random_numbers) == 10)
	
	def test_default_group_params(self):
		self.assertTrue(self.miller_rabin_test(eos_sgjjr.crypto.DEFAULT_GROUP.p))
		q = eos_sgjjr.crypto.DEFAULT_GROUP.q
		self.assertEqual(eos_sgjjr.crypto.DEFAULT_GROUP.p, q * eos_sgjjr.bigint.TWO + eos_sgjjr.bigint.ONE)
		self.assertTrue(self.miller_rabin_test(q))
	
	def generate_plaintext(self):
		return eos_sgjjr.bigint.noncrypto_random(eos_sgjjr.bigint.ONE, eos_sgjjr.crypto.DEFAULT_GROUP.p - eos_sgjjr.bigint.ONE)
	
	def test_cpseg(self):
		# s = a + c*r
		# s < p + (max 256-bit)*p
		# s < p*(max 256-bit + 1)
		MAX_SIGNATURE = eos_sgjjr.bigint.BigInt('10000000000000000000000000000000000000000000000000000000000000000', 16) * eos_sgjjr.crypto.DEFAULT_GROUP.p
		
		for i in range(CryptoTest.TARGET_BASIC):
			pt = self.generate_plaintext()
			#print('Round {} plaintext {}'.format(i, pt))
			sk = eos_sgjjr.crypto.CPSEGPrivateKey.generate()
			ct = sk.public_key.encrypt(pt)
			
			# Check that the signature makes sense
			self.assertTrue(ct.s > eos_sgjjr.bigint.ZERO)
			self.assertTrue(ct.s < MAX_SIGNATURE)
			
			m = sk.decrypt(ct)
			self.assertEqual(pt, m)
	
	def test_cpseg_replace(self):
		for i in range(CryptoTest.TARGET_BASIC):
			pt1 = self.generate_plaintext()
			pt2 = self.generate_plaintext()
			#print('Round {} plaintexts {} and {}'.format(i, pt1, pt2))
			sk = eos_sgjjr.crypto.CPSEGPrivateKey.generate()
			ct1 = sk.public_key.encrypt(pt1)
			ct2 = sk.public_key.encrypt(pt2)
			ct = eos_sgjjr.crypto.CPSEGCiphertext(public_key=ct1.public_key, R=ct2.R, Y=ct2.Y, A=ct1.A, s=ct1.s)
			with self.assertRaisesRegex(Exception, 'Signature is incorrect'):
				sk.decrypt(ct)
	
	def test_cpseg_homomorphic(self):
		for i in range(CryptoTest.TARGET_BASIC):
			pt = self.generate_plaintext()
			#print('Round {} plaintext {}'.format(i, pt))
			sk = eos_sgjjr.crypto.CPSEGPrivateKey.generate()
			ct = sk.public_key.encrypt(pt)
			# ElGamal is multiplicatively homomorphic
			ct2 = eos_sgjjr.crypto.CPSEGCiphertext(public_key=ct.public_key, R=pow(ct.R, eos_sgjjr.bigint.TWO, sk.public_key.group.p), Y=pow(ct.Y, eos_sgjjr.bigint.TWO, sk.public_key.group.p), A=ct.A, s=ct.s)
			with self.assertRaisesRegex(Exception, 'Signature is incorrect'):
				sk.decrypt(ct2)
	
	def test_cpseg_malformed(self):
		NEG_ONE = eos_sgjjr.bigint.BigInt('-1')
		
		def test_attrib(sk, ct, attrib):
			ct2 = eos_sgjjr.crypto.CPSEGCiphertext(public_key=ct.public_key, R=ct.R, Y=ct.Y, A=ct.A, s=ct.s)
			setattr(ct2, attrib, sk.public_key.group.p - eos_sgjjr.bigint.ONE)
			with self.assertRaisesRegex(Exception, 'Signature is incorrect'):
				sk.decrypt(ct2)
			setattr(ct2, attrib, sk.public_key.group.p)
			with self.assertRaisesRegex(Exception, 'Ciphertext is malformed'):
				sk.decrypt(ct2)
			setattr(ct2, attrib, sk.public_key.group.p + eos_sgjjr.bigint.ONE)
			with self.assertRaisesRegex(Exception, 'Ciphertext is malformed'):
				sk.decrypt(ct2)
			setattr(ct2, attrib, eos_sgjjr.bigint.ONE)
			with self.assertRaisesRegex(Exception, 'Signature is incorrect'):
				sk.decrypt(ct2)
			setattr(ct2, attrib, eos_sgjjr.bigint.ZERO)
			with self.assertRaisesRegex(Exception, 'Ciphertext is malformed'):
				sk.decrypt(ct2)
			setattr(ct2, attrib, NEG_ONE)
			with self.assertRaisesRegex(Exception, 'Ciphertext is malformed'):
				sk.decrypt(ct2)
		
		for i in range(CryptoTest.TARGET_BASIC):
			pt = self.generate_plaintext()
			sk = eos_sgjjr.crypto.CPSEGPrivateKey.generate()
			ct = sk.public_key.encrypt(pt)
			test_attrib(sk, ct, 'R')
			test_attrib(sk, ct, 'Y')
			test_attrib(sk, ct, 'A')
	
	def test_pvss_basic(self):
		k = 2
		n = 3
		
		trustees = [[eos_sgjjr.crypto.EGPrivateKey.generate(), eos_sgjjr.crypto.PVSSThresholdSetup(eos_sgjjr.crypto.DEFAULT_GROUP, k, n), None, None] for _ in range(n)]
		
		# Generate trustee private keys
		# 0: private key, 1: setup, 2: threshold private key, 3: partial decryption
		trustees = [[eos_sgjjr.crypto.EGPrivateKey.generate(), eos_sgjjr.crypto.PVSSThresholdSetup(eos_sgjjr.crypto.DEFAULT_GROUP, k, n), None, None] for _ in range(n)]
		
		# Add public keys
		for i in range(n):
			for j in range(n):
				trustees[i][1].add_trustee(j, trustees[j][0].public_key)
		
		# Generate commitments
		for i in range(n):
			commitment = trustees[i][1].generate_commitment()
			trustees[i][1].add_commitment(i, commitment)
			for j in range(n):
				trustees[j][1].add_commitment(i, commitment)
		
		# Verify commitments
		for i in range(n):
			trustees[i][1].verify_commitments(i, trustees[i][0])
		
		# Generate public key
		pk = trustees[0][1].generate_public_key()
		for i in range(n):
			trustees[i][2] = trustees[i][1].generate_private_key(i, trustees[i][0])
		
		# Check sk corresponds to pk
		polynomial = eos_sgjjr.crypto.Polynomial.combine(*[x.f for x in trustees[0][1].commitments])
		sk = polynomial.value_at(0)
		self.assertEqual(pk.X, pow(pk.group.g, sk, pk.group.p))
		
		# Check each threshold sk = value of polynomial
		for i in range(n):
			self.assertEqual(trustees[i][2].x, polynomial.value_at(i + 1))
		
		# Check overall sk is sum of commitment contributions
		# x = sum(xi) -> PVSS stage
		sk2 = eos_sgjjr.bigint.ZERO
		for i in range(n):
			sk2 = (sk2 + trustees[0][1].commitments[i].f.value_at(0)) % pk.group.q
		self.assertEqual(sk, sk2)
		
		# Check Langrangeing:
		
		# sum(xi*lambda0iS) == x? -> TDH1 stage
		sk3 = eos_sgjjr.bigint.ZERO
		for i in range(k):
			term = (trustees[i][2].x * eos_sgjjr.crypto.TDH1DecryptionCombiner._lagrange_coefficient(list(range(1, k+1)), i + 1, 0, pk.group.q)) % pk.group.q
			sk3 = (sk3 + term) % pk.group.q
		self.assertEqual(sk, sk3)
	
	def test_pvss(self):
		k = 2
		n = 3
		
		# Generate trustee private keys
		# 0: private key, 1: setup, 2: threshold private key, 3: partial decryption
		trustees = [[eos_sgjjr.crypto.EGPrivateKey.generate(), eos_sgjjr.crypto.PVSSThresholdSetup(eos_sgjjr.crypto.DEFAULT_GROUP, k, n), None, None] for _ in range(n)]
		
		# Add public keys
		for i in range(n):
			for j in range(n):
				trustees[i][1].add_trustee(j, trustees[j][0].public_key)
		
		# Generate commitments
		for i in range(n):
			commitment = trustees[i][1].generate_commitment()
			trustees[i][1].add_commitment(i, commitment)
			for j in range(n):
				trustees[j][1].add_commitment(i, commitment)
		
		# Verify commitments
		for i in range(n):
			trustees[i][1].verify_commitments(i, trustees[i][0])
		
		# Generate keys
		pk = trustees[0][1].generate_public_key()
		for i in range(n):
			trustees[i][2] = trustees[i][1].generate_private_key(i, trustees[i][0])
		
		# Encrypt message
		message = eos_sgjjr.bigint.BigInt('1337')
		ct = pk.encrypt(message)
		
		# Decrypt message
		for i in range(n):
			decryption = trustees[i][2].decrypt(ct)
			decryption.verify(ct)
			trustees[i][3] = decryption
		
		# Combine decryptions
		combiner = eos_sgjjr.crypto.TDH1DecryptionCombiner(ct, k, n)
		for i in range(k):
			combiner.add_partial_decryption(i, trustees[i][3])
		pt = combiner.decrypt()
		
		self.assertEqual(message, pt)
