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

__pragma__ = lambda x: None
__pragma__('opov')

import eos_core
if not eos_core.is_python:
	# TNYI: No pow() support
	def pow(a, b, c=None):
		return a.__pow__(b, c)

import eos_core.hashing
import eos_core.libobjects
import eos_sgjjr.bigint

class CyclicGroup(eos_core.libobjects.EosDictObject):
	class EosMeta:
		eos_name = 'eos_sgjjr.crypto.CyclicGroup'
		eos_fields = [
			eos_core.libobjects.EosField(eos_sgjjr.bigint.BigInt, 'p'),
			eos_core.libobjects.EosField(eos_sgjjr.bigint.BigInt, 'g'),
		]
	
	@property
	def q(self):
		# p = 2q + 1
		return (self.p - eos_sgjjr.bigint.ONE) // eos_sgjjr.bigint.TWO
	
	def random_element(self, crypto_random=True):
		crypto_method = eos_sgjjr.bigint.crypto_random if crypto_random else eos_sgjjr.bigint.noncrypto_random
		return crypto_method(eos_sgjjr.bigint.ONE, self.p - eos_sgjjr.bigint.ONE)

# RFC 3526
DEFAULT_GROUP = CyclicGroup(
	p=eos_sgjjr.bigint.BigInt('FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497CEA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF', 16),
	g=eos_sgjjr.bigint.TWO
)

class EGPublicKey(eos_core.libobjects.EosDictObject):
	class EosMeta:
		eos_name = 'eos_sgjjr.crypto.EGPublicKey'
		eos_fields = [
			eos_core.libobjects.EosField(CyclicGroup, 'group'),
			eos_core.libobjects.EosField(eos_sgjjr.bigint.BigInt, 'X'),
		]
	
	# HAC 8.18
	def encrypt(self, message):
		# Choose an element 1 <= k <= p - 2
		k = eos_sgjjr.bigint.crypto_random(eos_sgjjr.bigint.ONE, self.group.p - eos_sgjjr.bigint.TWO)
		
		gamma = pow(self.group.g, k, self.group.p)
		delta = (message * pow(self.X, k, self.group.p)) % self.group.p
		
		return EGCiphertext(public_key=self, gamma=gamma, delta=delta)

class EGPrivateKey(eos_core.libobjects.EosDictObject):
	class EosMeta:
		eos_name = 'eos_sgjjr.crypto.EGPrivateKey'
		eos_fields = [
			eos_core.libobjects.EosField(EGPublicKey, 'public_key'),
			eos_core.libobjects.EosField(eos_sgjjr.bigint.BigInt, 'x'),
		]
	
	# HAC 8.17
	@staticmethod
	def generate():
		# Choose an element 1 <= x <= p - 2
		x = eos_sgjjr.bigint.crypto_random(eos_sgjjr.bigint.ONE, DEFAULT_GROUP.p - eos_sgjjr.bigint.TWO)
		# Calculate the public key as G^x
		X = pow(DEFAULT_GROUP.g, x, DEFAULT_GROUP.p)
		
		pk = EGPublicKey(group=DEFAULT_GROUP, X=X)
		sk = EGPrivateKey(public_key=pk, x=x)
		return sk
	
	# HAC 8.18
	def decrypt(self, ciphertext):
		if (
			ciphertext.gamma <= eos_sgjjr.bigint.ZERO or ciphertext.gamma >= self.public_key.group.p or
			ciphertext.delta <= eos_sgjjr.bigint.ZERO or ciphertext.delta >= self.public_key.group.p
			):
			raise Exception('Ciphertext is malformed')
		
		gamma_inv = pow(ciphertext.gamma, self.public_key.group.p - eos_sgjjr.bigint.ONE - self.x, self.public_key.group.p)
		
		return (gamma_inv * ciphertext.delta) % self.public_key.group.p

# DKG from:
# GENNARO, Rosario, JARECKI, Stanisław, KRAWCZYK, Hugo and RABIN, Tal. Secure Distributed Key Generation for Discrete-Log Based Cryptosystems. In: *Journal of Cryptology*. Springer. 2007, **20**(1), 51–83. Available from: https://doi.org/10.1007/s00145-006-0347-3. Also available from: https://groups.csail.mit.edu/cis/pubs/stasio/vss.ps.gz.

class Polynomial:
	def __init__(self, modulus, coefficients):
		self.modulus = modulus
		self.coefficients = coefficients
	
	@property
	def degree(self):
		return len(self.coefficients) - 1
	
	def value_at(self, x):
		value = eos_sgjjr.bigint.ZERO
		for i in range(0, self.degree + 1):
			value = (value + (self.coefficients[i] * pow(eos_sgjjr.bigint.BigInt(x), eos_sgjjr.bigint.BigInt(i), self.modulus)) % self.modulus) % self.modulus
		return value
	
	@staticmethod
	def generate(modulus, degree):
		coefficients = []
		for i in range(0, degree + 1):
			coefficients.append(eos_sgjjr.bigint.crypto_random(eos_sgjjr.bigint.ONE, modulus - eos_sgjjr.bigint.ONE))
		return Polynomial(modulus, coefficients)
	
	@staticmethod
	def combine(*args):
		polynomial = Polynomial(args[0].modulus, [eos_sgjjr.bigint.ZERO] * len(args[0].coefficients))
		for item in args:
			for coeff in range(len(polynomial.coefficients)):
				polynomial.coefficients[coeff] = (polynomial.coefficients[coeff] + item.coefficients[coeff]) % polynomial.modulus
		return polynomial

# Pedersen-VSS from:
# https://www.cryptoworkshop.com/ximix/lib/exe/fetch.php?media=pedersen.pdf

class PVSSThresholdCommitment:
	def __init__(self, group, k, n):
		self.group = group
		self.public = [None] * k
		self.verification = [None] * (n + 1)
		self.private = [None] * n
		#self.private_pt = [None] * n # For debugging!!
		#self.f = None # For debugging!!

class PVSSThresholdSetup:
	def __init__(self, group, k, n):
		self.group = group
		self.k = k
		self.trustees = [None] * n
		self.commitments = [None] * n
	
	def add_trustee(self, index, public_key):
		self.trustees[index] = public_key
	
	def generate_commitment(self):
		commitment = PVSSThresholdCommitment(self.group, self.k, len(self.trustees))
		# Generate a random polynomial
		f = Polynomial.generate(self.group.q, self.k - 1)
		#commitment.f = f
		# Generate public factors
		for i in range(0, self.k):
			commitment.public[i] = pow(self.group.g, f.coefficients[i], self.group.p)
		# Generate verification factors: verification[0] == public[0]
		for i in range(0, len(self.trustees) + 1):
			commitment.verification[i] = pow(self.group.g, f.value_at(i), self.group.p)
		# Encrypt private factors
		for i in range(1, len(self.trustees) + 1):
			value = f.value_at(i)
			#commitment.private_pt[i - 1] = value
			commitment.private[i - 1] = self.trustees[i - 1].encrypt(value)
		return commitment
	
	def add_commitment(self, index, commitment):
		self.commitments[index] = commitment
	
	def verify_commitments(self, index, private_key):
		for j in range(0, len(self.trustees)):
			value = private_key.decrypt(self.commitments[j].private[index])
			lhs = pow(self.group.g, value, self.group.p)
			
			rhs = eos_sgjjr.bigint.ONE
			for l in range(0, self.k):
				# index + 1 because values start from 1
				rhs = (rhs * pow(self.commitments[j].public[l], pow(index + 1, l), self.group.p)) % self.group.p
			
			if lhs != rhs:
				raise Exception('Invalid commitment by trustee {}'.format(j))
	
	def generate_public_key(self):
		value = eos_sgjjr.bigint.ONE
		h = [eos_sgjjr.bigint.ONE] * len(self.trustees)
		
		for i in range(0, len(self.trustees)):
			value = (value * self.commitments[i].public[0]) % self.group.p
			for j in range(0, len(self.trustees)):
				h[j] = (h[j] * self.commitments[i].verification[j + 1]) % self.group.p # verification items 1 to n
		
		return TDH1PublicKey(group=self.group, X=value, h=h)
		#return TDH1PublicKey(group=SMALL_GROUP, X=value, h=h)
	
	def generate_private_key(self, index, private_key):
		value = eos_sgjjr.bigint.ZERO
		for i in range(0, len(self.trustees)):
			current_value = private_key.decrypt(self.commitments[i].private[index])
			#assert current_value == self.commitments[i].private_pt[index]
			value = (value + current_value) % self.group.q
		return TDH1PrivateKey(public_key=self.generate_public_key(), i=index, x=value)

# TDH1 cryptosystem from:
# SHOUP, Victor and GENNARO, Rosario. Securing Threshold Cryotpsystems against Chosen Ciphertext Attack. In: *Journal of Cryptology*. Springer, 2002, **15**(2), 75–96. Available from: https://doi.org/10.1007/s00145-001-0020-9. Also available from: http://www.shoup.net/papers/thresh1.pdf.

class TDH1PublicKey(eos_core.libobjects.EosDictObject):
	class EosMeta:
		eos_name = 'eos_sgjjr.crypto.TDH1PublicKey'
		eos_fields = [
			eos_core.libobjects.EosField(CyclicGroup, 'group'),
			eos_core.libobjects.EosField(eos_sgjjr.bigint.BigInt, 'X'),
			eos_core.libobjects.EosField(eos_sgjjr.bigint.BigInt, 'h'), # verification factors
		]
	
	def encrypt(self, message):
		# Choose two elements from Z*p
		r = self.group.random_element()
		s = self.group.random_element()
		
		c = eos_sgjjr.bigint.BigInt(eos_core.hashing.hash_as_hex(str(pow(self.X, r, self.group.p))), 16) ^ message
		u = pow(self.group.g, r, self.group.p)
		w = pow(self.group.g, s, self.group.p)
		gb = eos_sgjjr.bigint.BigInt(eos_core.hashing.hash_as_hex(str(c), str(u), str(w)), 16) # We don't use labels
		ub = pow(gb, r, self.group.p)
		wb = pow(gb, s, self.group.p)
		e = eos_sgjjr.bigint.BigInt(eos_core.hashing.hash_as_hex(str(gb), str(ub), str(wb)), 16)
		# Confusingly, this is not mod p!!!
		f = s + r*e
		
		return TDH1Ciphertext(public_key=self, c=c, u=u, ub=ub, e=e, f=f)

class TDH1PrivateKey(eos_core.libobjects.EosDictObject):
	class EosMeta:
		eos_name = 'eos_sgjjr.crypto.TDH1PrivateKey'
		eos_fields = [
			eos_core.libobjects.EosField(TDH1PublicKey, 'public_key'),
			eos_core.libobjects.EosField(int, 'i'),
			eos_core.libobjects.EosField(eos_sgjjr.bigint.BigInt, 'x'),
		]
	
	def decrypt(self, ciphertext):
		if not ciphertext.is_well_formed():
			raise Exception('Ciphertext does not verify')
		
		# Now decrypt and prove
		si = self.public_key.group.random_element()
		ui = pow(ciphertext.u, self.x, self.public_key.group.p)
		uhi = pow(ciphertext.u, si, self.public_key.group.p)
		hhi = pow(self.public_key.group.g, si, self.public_key.group.p)
		ei = eos_sgjjr.bigint.BigInt(eos_core.hashing.hash_as_hex(str(ui), str(uhi), str(hhi)), 16)
		fi = si + self.x*ei
		
		return TDH1PartialDecryption(i=self.i, ui=ui, ei=ei, fi=fi)

class TDH1PartialDecryption(eos_core.libobjects.EosDictObject):
	class EosMeta:
		eos_name = 'eos_sgjjr.crypto.TDH1PartialDecryption'
		eos_fields = [
			eos_core.libobjects.EosField(int, 'i'),
			eos_core.libobjects.EosField(eos_sgjjr.bigint.BigInt, 'ui'),
			eos_core.libobjects.EosField(eos_sgjjr.bigint.BigInt, 'ei'),
			eos_core.libobjects.EosField(eos_sgjjr.bigint.BigInt, 'fi'),
		]
	
	def verify(self, ciphertext):
		if not ciphertext.is_well_formed():
			raise Exception('Ciphertext does not verify')
		
		ufi = pow(ciphertext.u, self.fi, ciphertext.public_key.group.p)
		uiei = pow(self.ui, self.ei, ciphertext.public_key.group.p)
		uiei_inv = pow(uiei, ciphertext.public_key.group.p - eos_sgjjr.bigint.TWO, ciphertext.public_key.group.p)
		uhi = (ufi * uiei_inv) % ciphertext.public_key.group.p
		
		gfi = pow(ciphertext.public_key.group.g, self.fi, ciphertext.public_key.group.p)
		hiei = pow(ciphertext.public_key.h[self.i], self.ei, ciphertext.public_key.group.p)
		hiei_inv = pow(hiei, ciphertext.public_key.group.p - eos_sgjjr.bigint.TWO, ciphertext.public_key.group.p)
		hhi = (gfi * hiei_inv) % ciphertext.public_key.group.p
		
		ei_expected = eos_sgjjr.bigint.BigInt(eos_core.hashing.hash_as_hex(str(self.ui), str(uhi), str(hhi)), 16)
		if self.ei != ei_expected:
			raise Exception('Decryption proof is invalid')
			#pass

class EGCiphertext(eos_core.libobjects.EosDictObject):
	class EosMeta:
		eos_name = 'eos_sgjjr.crypto.EGCiphertext'
		eos_fields = [
			eos_core.libobjects.EosField(EGPublicKey, 'public_key'),
			eos_core.libobjects.EosField(eos_sgjjr.bigint.BigInt, 'gamma'), # G^k
			eos_core.libobjects.EosField(eos_sgjjr.bigint.BigInt, 'delta'), # M X^k
		]

class TDH1Ciphertext(EGCiphertext):
	class EosMeta:
		eos_name = 'eos_sgjjr.crypto.TDH1Ciphertext'
		eos_fields = [
			eos_core.libobjects.EosField(EGPublicKey, 'public_key'),
			eos_core.libobjects.EosField(eos_sgjjr.bigint.BigInt, 'c'),
			eos_core.libobjects.EosField(eos_sgjjr.bigint.BigInt, 'u'),
			eos_core.libobjects.EosField(eos_sgjjr.bigint.BigInt, 'ub'),
			eos_core.libobjects.EosField(eos_sgjjr.bigint.BigInt, 'e'),
			eos_core.libobjects.EosField(eos_sgjjr.bigint.BigInt, 'f'),
		]
	
	def is_well_formed(self):
		# Compute w
		gf = pow(self.public_key.group.g, self.f, self.public_key.group.p)
		ue = pow(self.u, self.e, self.public_key.group.p)
		ue_inv = pow(ue, self.public_key.group.p - eos_sgjjr.bigint.TWO, self.public_key.group.p)
		w = (gf * ue_inv) % self.public_key.group.p
		
		# Compute gb
		gb = eos_sgjjr.bigint.BigInt(eos_core.hashing.hash_as_hex(str(self.c), str(self.u), str(w)), 16)
		
		# Compute wb
		gbf = pow(gb, self.f, self.public_key.group.p)
		ube = pow(self.ub, self.e, self.public_key.group.p)
		ube_inv = pow(ube, self.public_key.group.p - eos_sgjjr.bigint.TWO, self.public_key.group.p)
		wb = (gbf * ube_inv) % self.public_key.group.p
		
		# Verify e
		e_expected = eos_sgjjr.bigint.BigInt(eos_core.hashing.hash_as_hex(str(gb), str(self.ub), str(wb)), 16)
		if self.e != e_expected:
			return False
		
		return True

class TDH1DecryptionCombiner:
	def __init__(self, ciphertext, k, n):
		if not ciphertext.is_well_formed():
			raise Exception('Ciphertext does not verify')
		self.ciphertext = ciphertext
		
		self.k = k
		self.n = n
		self.partial_decryptions = []
	
	def add_partial_decryption(self, index, partial_decryption):
		self.partial_decryptions.append((index, partial_decryption))
	
	# From ThresholdDecryptionCombinator in PloneVoteCryptoLib, by Lazaro Clapp, licensed under the MIT licence
	@staticmethod
	def _lagrange_coefficient(indexes, i, x, prime_modulus):
		# We calculate the whole coefficient as a fraction and the take the inverse 
		# of the denominator in Z_{prime_modulus}, rather than inverting each (i-j)  
		numerator = eos_sgjjr.bigint.ONE
		denominator = eos_sgjjr.bigint.ONE
		
		for j in indexes:
			if(i == j):
				continue
			numerator *= (x - j)
			denominator *= (i - j)
		
		numerator = numerator % prime_modulus
		denominator = denominator % prime_modulus
		# a^(p-2) is the inverse of a in Z_{p} with p prime. Proof:
		# (a)(a^(p-2)) = a^(p-1) = 1
		inv_denominator = pow(denominator, prime_modulus - eos_sgjjr.bigint.TWO, prime_modulus)
		
		result = (numerator*inv_denominator) % prime_modulus
		return result
	
	def decrypt(self):
		# TODO: Select k elements
		S = self.partial_decryptions
		indexes = [trustee[0] + 1 for trustee in S]
		
		value = eos_sgjjr.bigint.ONE
		for trustee in S:
			# polynomial is 1-based
			# NB: Secret-key is q-based!
			lambda0iS = TDH1DecryptionCombiner._lagrange_coefficient(indexes, trustee[0] + 1, 0, self.ciphertext.public_key.group.q)
			uil = pow(trustee[1].ui, lambda0iS, self.ciphertext.public_key.group.p)
			value = (value * uil) % self.ciphertext.public_key.group.p
		
		hashed = eos_sgjjr.bigint.BigInt(eos_core.hashing.hash_as_hex(str(value)), 16)
		return (hashed ^ self.ciphertext.c)
