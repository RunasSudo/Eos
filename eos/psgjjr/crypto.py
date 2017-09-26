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

class CyclicGroup(EmbeddedObject):
	p = EmbeddedObjectField(BigInt)
	g = EmbeddedObjectField(BigInt)
	
	@property
	def q(self):
		# p = 2q + 1
		return (self.p - ONE) // TWO
	
	def random_element(self, crypto_random=True):
		crypto_method = BigInt.crypto_random if crypto_random else BigInt.noncrypto_random
		return crypto_method(ONE, self.p - ONE)

# RFC 3526
DEFAULT_GROUP = CyclicGroup(
	p=BigInt('FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497CEA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF', 16),
	g=TWO
)

class EGPublicKey(EmbeddedObject):
	group = EmbeddedObjectField(CyclicGroup)
	X = EmbeddedObjectField(BigInt)
	
	# HAC 8.18
	def encrypt(self, message):
		message += ONE # Dodgy hack to allow zeroes
		
		if message <= ZERO:
			raise Exception('Invalid message')
		if message >= self.group.p:
			raise Exception('Invalid message')
		
		# Choose an element 1 <= k <= p - 2
		k = BigInt.crypto_random(ONE, self.group.p - TWO)
		
		gamma = pow(self.group.g, k, self.group.p)
		delta = (message * pow(self.X, k, self.group.p)) % self.group.p
		
		return EGCiphertext(public_key=self, gamma=gamma, delta=delta)

class EGPrivateKey(EmbeddedObject):
	public_key = EmbeddedObjectField(EGPublicKey)
	x = EmbeddedObjectField(BigInt)
	
	# HAC 8.17
	@staticmethod
	def generate(group=DEFAULT_GROUP):
		# Choose an element 1 <= x <= p - 2
		x = BigInt.crypto_random(ONE, group.p - TWO)
		# Calculate the public key as G^x
		X = pow(group.g, x, group.p)
		
		pk = EGPublicKey(group=group, X=X)
		sk = EGPrivateKey(public_key=pk, x=x)
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
		return pt - ONE

class EGCiphertext(EmbeddedObject):
	public_key = EmbeddedObjectField(EGPublicKey)
	gamma = EmbeddedObjectField(BigInt) # G^k
	delta = EmbeddedObjectField(BigInt) # M X^k
