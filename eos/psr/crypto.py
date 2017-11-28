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
from eos.base.election import *

class CyclicGroup(EmbeddedObject):
	p = EmbeddedObjectField(BigInt)
	g = EmbeddedObjectField(BigInt)
	
	@property
	def q(self):
		# p = 2q + 1
		return (self.p - ONE) / TWO
	
	def random_Zp_element(self, crypto_random=True):
		crypto_method = BigInt.crypto_random if crypto_random else BigInt.noncrypto_random
		return crypto_method(ONE, self.p - ONE)
	
	def random_Zps_element(self, crypto_random=True):
		crypto_method = BigInt.crypto_random if crypto_random else BigInt.noncrypto_random
		# Z_p* = {1..p-1} provided that p is a prime
		return crypto_method(ONE, self.p - ONE)
	
	def random_Zq_element(self, crypto_random=True):
		crypto_method = BigInt.crypto_random if crypto_random else BigInt.noncrypto_random
		return crypto_method(ZERO, self.q - ONE)

# RFC 3526
DEFAULT_GROUP = CyclicGroup(
	p=BigInt('FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497CEA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF', 16),
	g=TWO
)

class EGPublicKey(EmbeddedObject):
	group = EmbeddedObjectField(CyclicGroup)
	X = EmbeddedObjectField(BigInt)
	
	def nbits(self):
		# Our messages are restricted to G_q
		return self.group.q.nbits() - 1
	
	# HAC 8.18
	def _encrypt(self, message, randomness=None):
		if message <= ZERO:
			raise Exception('Invalid message')
		if message >= self.group.p:
			raise Exception('Invalid message')
		
		if randomness is None:
			# Choose an element 1 <= k <= p - 2
			k = BigInt.crypto_random(ONE, self.group.p - TWO)
		else:
			k = randomness
		
		gamma = pow(self.group.g, k, self.group.p)
		delta = (message * pow(self.X, k, self.group.p)) % self.group.p
		
		return EGCiphertext(public_key=self, gamma=gamma, delta=delta, m0=message, randomness=k)
	
	# Adida 2008
	def message_to_m0(self, message):
		m0 = message + ONE
		
		if pow(m0, self.group.q, self.group.p) == ONE:
			# m0 is already in G_q
			return m0
		else:
			# For the life of me I can't find any reputable references for this aside from Adida 2008...
			m0 = (-m0) % self.group.p
			return m0
	
	def m0_to_message(self, m0):
		if m0 < self.group.q:
			return m0 - ONE
		else:
			return ((-m0) % self.group.p) - ONE
	
	def encrypt(self, message, randomness=None):
		if message < ZERO:
			raise Exception('Invalid message')
		if message >= self.group.q:
			raise Exception('Invalid message')
		
		return self._encrypt(self.message_to_m0(message), randomness)

class EGPrivateKey(EmbeddedObject):
	pk_class = EGPublicKey
	
	public_key = EmbeddedObjectField(EGPublicKey)
	x = EmbeddedObjectField(BigInt)
	
	# HAC 8.17
	@classmethod
	def generate(cls, group=DEFAULT_GROUP):
		# Choose an element 1 <= x <= p - 2
		x = BigInt.crypto_random(ONE, group.p - TWO)
		# Calculate the public key as G^x
		X = pow(group.g, x, group.p)
		
		pk = cls.pk_class(group=group, X=X)
		sk = cls(public_key=pk, x=x)
		return sk
	
	# HAC 8.18
	def decrypt(self, ciphertext):
		if (
			ciphertext.gamma <= ZERO or ciphertext.gamma >= self.public_key.group.p or
			ciphertext.delta <= ZERO or ciphertext.delta >= self.public_key.group.p
			):
			raise Exception('Ciphertext is malformed')
		
		gamma_inv = pow(ciphertext.gamma, self.public_key.group.p - ONE - self.x, self.public_key.group.p)
		
		pt = (gamma_inv * ciphertext.delta) % self.public_key.group.p
		
		# Undo the encryption mapping
		return self.public_key.m0_to_message(pt)

class EGCiphertext(EmbeddedObject):
	public_key = EmbeddedObjectField(EGPublicKey)
	gamma = EmbeddedObjectField(BigInt) # G^k
	delta = EmbeddedObjectField(BigInt) # M X^k
	
	randomness = EmbeddedObjectField(BigInt, is_hashed=False)
	m0 = EmbeddedObjectField(BigInt, is_hashed=False)
	
	def reencrypt(self, k=None):
		# Generate an encryption of one
		if k is None:
			k = BigInt.crypto_random(ONE, self.public_key.group.p - TWO)
		gamma = pow(self.public_key.group.g, k, self.public_key.group.p)
		delta = pow(self.public_key.X, k, self.public_key.group.p)
		
		return EGCiphertext(public_key=self.public_key, gamma=((self.gamma * gamma) % self.public_key.group.p), delta=((self.delta * delta) % self.public_key.group.p)), k
	
	def deaudit(self):
		return EGCiphertext(public_key=self.public_key, gamma=self.gamma, delta=self.delta)
	
	def is_randomness_valid(self):
		ct = self.public_key._encrypt(self.m0, self.randomness)
		return ct.gamma == self.gamma and ct.delta == self.delta

# Signed ElGamal per Schnorr & Jakobssen
class SEGPublicKey(EGPublicKey):
	def _encrypt(self, message, randomness=None):
		if randomness is None:
			# Choose an element 1 <= k <= p - 2
			r = BigInt.crypto_random(ONE, self.group.p - TWO)
		else:
			r = randomness
		s = BigInt.crypto_random(ONE, self.group.p - TWO)
		
		gamma = pow(self.group.g, r, self.group.p) # h
		delta = (message * pow(self.X, r, self.group.p)) % self.group.p # f
		
		c = SHA256().update_bigint(pow(self.group.g, s, self.group.p), gamma, delta).hash_as_bigint()
		
		z = s + c*r
		
		return SEGCiphertext(public_key=self, gamma=gamma, delta=delta, c=c, z=z, m0=message, randomness=r)

class SEGPrivateKey(EGPrivateKey):
	pk_class = SEGPublicKey

class SEGCiphertext(EGCiphertext):
	public_key = EmbeddedObjectField(SEGPublicKey)
	c = EmbeddedObjectField(BigInt)
	z = EmbeddedObjectField(BigInt)
	
	def is_signature_valid(self):
		gs = (pow(self.public_key.group.g, self.z, self.public_key.group.p) * pow(self.gamma, self.public_key.group.p - ONE - self.c, self.public_key.group.p)) % self.public_key.group.p
		c = SHA256().update_bigint(gs, self.gamma, self.delta).hash_as_bigint()
		
		return self.c == c
	
	def deaudit(self):
		return SEGCiphertext(public_key=self.public_key, gamma=self.gamma, delta=self.delta, c=self.c, z=self.z)

class Polynomial(EmbeddedObject):
	coefficients = EmbeddedObjectListField(BigInt) # x^0, x^1, ... x^n
	modulus = EmbeddedObjectField(BigInt)
	
	def value(self, x):
		if not isinstance(x, BigInt):
			x = BigInt(x)
		
		result = ZERO
		for i in range(len(self.coefficients)):
			#result = (result + ((self.coefficients[i] * pow(x, i, self.modulus)) % self.modulus)) % self.modulus
			result = result + (self.coefficients[i] * pow(x, i))
		return result

class PedersenVSSPrivateKey(EmbeddedObject):
	public_key = EmbeddedObjectField(SEGPublicKey)
	
	x = EmbeddedObjectField(BigInt) # secret
	
	def get_modified_secret(self):
		mod_s = self.x
		for j in range(1, threshold + 1): # 1 to threshold
			...
	
	def decrypt(self, ciphertext):
		if (
			ciphertext.gamma <= ZERO or ciphertext.gamma >= self.public_key.group.p or
			ciphertext.delta <= ZERO or ciphertext.delta >= self.public_key.group.p
			):
			raise Exception('Ciphertext is malformed')
		
		gamma_inv = pow(ciphertext.gamma, self.public_key.group.p - ONE - self.x, self.public_key.group.p)
		return gamma_inv
