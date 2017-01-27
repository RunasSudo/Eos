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

import django.test

class CryptoTest(django.test.TestCase):
	TARGET_BASIC = 3
	
	def generate_plaintext(self):
		return eos_stjjr.bigint.noncrypto_random(1, eos_stjjr.crypto.DEFAULT_GROUP.p - 1)
	
	def test_cpseg(self):
		for i in range(CryptoTest.TARGET_BASIC):
			pt = self.generate_plaintext()
			print('Round {} plaintext {}'.format(i, pt))
			sk = eos_stjjr.crypto.CPSEGPrivateKey.generate()
			ct = sk.public_key.encrypt(pt)
			m = sk.decrypt(ct)
			self.assertEqual(pt, m)
	
	def test_cpseg_replace(self):
		for i in range(CryptoTest.TARGET_BASIC):
			pt1 = self.generate_plaintext()
			pt2 = self.generate_plaintext()
			print('Round {} plaintexts {} and {}'.format(i, pt1, pt2))
			sk = eos_stjjr.crypto.CPSEGPrivateKey.generate()
			ct1 = sk.public_key.encrypt(pt1)
			ct2 = sk.public_key.encrypt(pt2)
			ct = eos_stjjr.crypto.CPSEGCiphertext(public_key=ct1.public_key, R=ct2.R, Y=ct2.Y, A=ct1.A, s=ct1.s)
			with self.assertRaisesMessage(Exception, 'Signature is incorrect'):
				sk.decrypt(ct)
	
	def test_cpseg_homomorphic(self):
		for i in range(CryptoTest.TARGET_BASIC):
			pt = self.generate_plaintext()
			print('Round {} plaintext {}'.format(i, pt))
			sk = eos_stjjr.crypto.CPSEGPrivateKey.generate()
			ct = sk.public_key.encrypt(pt)
			# ElGamal is multiplicatively homomorphic
			ct2 = eos_stjjr.crypto.CPSEGCiphertext(public_key=ct.public_key, R=pow(ct.R, eos_stjjr.bigint.TWO, sk.public_key.group.p), Y=pow(ct.Y, eos_stjjr.bigint.TWO, sk.public_key.group.p), A=ct.A, s=ct.s)
			with self.assertRaisesMessage(Exception, 'Signature is incorrect'):
				sk.decrypt(ct2)
