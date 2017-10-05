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
from eos.psr.crypto import *
from eos.psr.bitstream import *

class PedersenVSSSetup:
	def __init__(self):
		self.group = None
		self.participants = []
		self.threshold = 0
		
		self.public_key = None
	
	def compute_public_key(self):
		h = ONE
		for participant in self.participants:
			h = (h * participant.h.val) % self.group.p
		
		self.public_key = SEGPublicKey(group=self.group, X=h)
		return self.public_key
	
	def combine_decryption(self, decryption_shares):
		gamma_inv = ONE
		for i, share in decryption_shares:
			lagrange_num = ONE
			lagrange_den = ONE
			for j, _ in decryption_shares:
				lagrange_num = lagrange_num * BigInt(j)
				lagrange_den = lagrange_den * BigInt(j - i)
			if lagrange_num % lagrange_den != 0:
				raise Exception('Cannot raise to fractional exponent')
			gamma_inv = gamma_inv * pow(share, lagrange_num / lagrange_den, self.group.p)

class PedersenVSSCommitment(EmbeddedObject):
	val = EmbeddedObjectField(BigInt)
	rand = EmbeddedObjectField(BigInt)

class PedersenVSSParticipant():
	def __init__(self, setup):
		self.setup = setup
		
		self.pk = None
		self.shares_received = []
		self.F = []
		
		self.h = None
		self.h_commitment = None
		
		self.sk = None # non-threshold
		self.threshold_sk = None
		self.f = Polynomial(modulus=self.setup.group.p)
	
	def commit_pk_share(self):
		# Generate random polynomial
		for _ in range(0, self.setup.threshold): # 0 to k-1
			coeff = self.setup.group.random_element()
			self.f.coefficients.append(coeff)
			#self.F.append(PedersenVSSCommitment(val=coeff, rand=self.sk.public_key.group.random_element()))
			self.F.append(pow(self.setup.group.g, coeff, self.setup.group.p))
		
		self.h = PedersenVSSCommitment(val=self.F[0], rand=self.setup.group.random_element())
		self.h_commitment = SHA256().update_obj(self.h).hash_as_bigint()
		
		return self.h_commitment
	
	def get_share_for(self, other_idx):
		other = self.setup.participants[other_idx]
		#return other.pk.encrypt(self.f.value(other_idx + 1) % self.setup.group.p)
		return BitStream().write_bigint(self.f.value(other_idx + 1)).multiple_of(other.pk.group.p.nbits(), True).map(other.pk.encrypt, other.pk.group.p.nbits())
	
	def compute_secret_key(self):
		x = ZERO
		for share in self.shares_received:
			x = (x + share) % self.setup.group.p
		self.threshold_sk = PedersenVSSPrivateKey(public_key=self.setup.public_key, x=x)
		return self.threshold_sk
