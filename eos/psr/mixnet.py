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
from eos.psr.election import *

class RPCMixnet:
	def __init__(self, mix_order):
		self.mix_order = mix_order
		
		self.is_left = (self.mix_order % 2 == 0)
		
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
		
		commitments = []
		if self.is_left:
			for i in range(len(permutations_and_reenc)):
				val = permutations_and_reenc[i]
				val_obj = MixChallengeResponse(challenge_index=i, response_index=val[0], reenc=val[1], rand=val[2])
				commitments.append(SHA256().update_obj(val_obj).hash_as_bigint())
		else:
			for i in range(len(permutations_and_reenc)):
				# Find the answer that went to 'i'
				idx = next(idx for idx in range(len(permutations_and_reenc)) if permutations_and_reenc[idx][0] == i)
				val = permutations_and_reenc[idx]
				
				val_obj = MixChallengeResponse(challenge_index=i, response_index=idx, reenc=val[1], rand=val[3])
				commitments.append(SHA256().update_obj(val_obj).hash_as_bigint())
		
		self.params = permutations_and_reenc
		return shuffled_answers, commitments
	
	def challenge(self, i):
		if self.is_left:
			val = self.params[i]
			return MixChallengeResponse(challenge_index=i, response_index=val[0], reenc=val[1], rand=val[2])
		else:
			idx = next(idx for idx in range(len(self.params)) if self.params[idx][0] == i)
			val = self.params[idx]
			return MixChallengeResponse(challenge_index=i, response_index=idx, reenc=val[1], rand=val[3])
