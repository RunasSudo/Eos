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
from eos.base.election import *

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
		return pt - ONE

class EGCiphertext(EmbeddedObject):
	public_key = EmbeddedObjectField(EGPublicKey)
	gamma = EmbeddedObjectField(BigInt) # G^k
	delta = EmbeddedObjectField(BigInt) # M X^k
	
	def reencrypt(self, k=None):
		# Generate an encryption of one
		if k is None:
			k = BigInt.crypto_random(ONE, self.public_key.group.p - TWO)
		gamma = pow(self.public_key.group.g, k, self.public_key.group.p)
		delta = pow(self.public_key.X, k, self.public_key.group.p)
		
		return EGCiphertext(public_key=self.public_key, gamma=((self.gamma * gamma) % self.public_key.group.p), delta=((self.delta * delta) % self.public_key.group.p)), k

# Signed ElGamal per Schnorr & Jakobssen
class SEGPublicKey(EGPublicKey):
	def encrypt(self, message):
		message += ONE # Dodgy hack to allow zeroes
		
		if message <= ZERO:
			raise Exception('Invalid message')
		if message >= self.group.p:
			raise Exception('Invalid message')
		
		# Choose an element 1 <= k <= p - 2
		r = BigInt.crypto_random(ONE, self.group.p - TWO)
		s = BigInt.crypto_random(ONE, self.group.p - TWO)
		
		gamma = pow(self.group.g, r, self.group.p) # h
		delta = (message * pow(self.X, r, self.group.p)) % self.group.p # f
		
		_, c = EosObject.to_sha256(str(pow(self.group.g, s, self.group.p)), str(gamma), str(delta))
		
		z = s + c*r
		
		return SEGCiphertext(public_key=self, gamma=gamma, delta=delta, c=c, z=z)

class SEGPrivateKey(EGPrivateKey):
	pk_class = SEGPublicKey

class SEGCiphertext(EGCiphertext):
	public_key = EmbeddedObjectField(SEGPublicKey)
	c = EmbeddedObjectField(BigInt)
	z = EmbeddedObjectField(BigInt)
	
	def is_signature_valid(self):
		gs = (pow(self.public_key.group.g, self.z, self.public_key.group.p) * pow(self.gamma, self.public_key.group.p - ONE - self.c, self.public_key.group.p)) % self.public_key.group.p
		_, c = EosObject.to_sha256(str(gs), str(self.gamma), str(self.delta))
		
		return self.c == c

class BlockEncryptedAnswer(EncryptedAnswer):
	blocks = EmbeddedObjectListField()
	
	def decrypt(self):
		# TODO
		raise Exception('NYI')

class RPCMixnet:
	def __init__(self):
		self.params = []
	
	def random_permutation(self, n):
		permutation = list(range(n))
		# Fisher-Yates shuffle
		i = n
		while i != 0:
			rnd = BigInt.crypto_random(0, i - 1)
			rnd = rnd.__int__()
			i -= 1
			permutation[rnd], permutation[i] = permutation[i], permutation[rnd]
		return permutation
	
	def shuffle(self, encrypted_answers):
		shuffled_answers = [None] * len(encrypted_answers)
		permutations = self.random_permutation(len(encrypted_answers))
		
		permutations_and_reenc = []
		
		for i in range(len(encrypted_answers)):
			encrypted_answer = encrypted_answers[i]
			
			# Reencrypt the answer
			shuffled_blocks = []
			block_reencryptions = []
			for block in encrypted_answer.blocks:
				block2, reenc = block.reencrypt()
				shuffled_blocks.append(block2)
				block_reencryptions.append(reenc)
			# And shuffle it to the new position
			shuffled_answers[permutations[i]] = BlockEncryptedAnswer(blocks=shuffled_blocks)
			# Record the parameters
			permutations_and_reenc.append([permutations[i], block_reencryptions, block.public_key.group.random_element(), block.public_key.group.random_element()])
		
		commitments_left = []
		for i in range(len(permutations_and_reenc)):
			val = permutations_and_reenc[i]
			val_json = [val[0], [str(x) for x in val[1]], str(val[2])]
			commitments_left.append(EosObject.to_sha256(EosObject.to_json(val_json))[0])
		
		commitments_right = []
		for i in range(len(permutations_and_reenc)):
			# Find the answer that went to 'i'
			idx = next(idx for idx in range(len(permutations_and_reenc)) if permutations_and_reenc[idx][0] == i)
			val = permutations_and_reenc[idx]
			
			val_json = [idx, [str(x) for x in val[1]], str(val[3])]
			commitments_right.append(EosObject.to_sha256(EosObject.to_json(val_json))[0])
		
		self.params = permutations_and_reenc
		return shuffled_answers, commitments_left, commitments_right
	
	def challenge(self, i, is_left):
		if is_left:
			val = self.params[i]
			return [val[0], val[1], val[2]]
		else:
			idx = next(idx for idx in range(len(self.params)) if self.params[idx][0] == i)
			val = self.params[idx]
			return [idx, val[1], val[3]]
