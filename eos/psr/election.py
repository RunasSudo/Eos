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
from eos.psr.bitstream import *
from eos.psr.crypto import *

from eos.core.objects import __pragma__

class BlockEncryptedAnswer(EncryptedAnswer):
	blocks = EmbeddedObjectListField()
	
	@classmethod
	def encrypt(cls, pk, obj):
		pt = EosObject.to_json(EosObject.serialise_and_wrap(obj))
		bs = BitStream()
		bs.write_string(pt)
		bs.multiple_of(pk.nbits(), True)
		ct = bs.map(pk.encrypt, pk.nbits())
		
		return cls(blocks=ct)
	
	def decrypt(self, sk=None):
		if sk is None:
			sk = self.recurse_parents(PSRElection).sk
		
		bs = BitStream.unmap(self.blocks, sk.decrypt, sk.public_key.nbits())
		m = bs.read_string()
		obj = EosObject.deserialise_and_unwrap(EosObject.from_json(m))
		
		return obj

class Trustee(EmbeddedObject):
	name = StringField()
	email = StringField()

class MixChallengeResponse(EmbeddedObject):
	challenge_index = IntField()
	response_index = IntField()
	reenc = EmbeddedObjectListField(BigInt)
	rand = EmbeddedObjectField(BigInt)

class MixingTrustee(Trustee):
	mixed_questions = ListField(EmbeddedObjectListField(BlockEncryptedAnswer), is_hashed=False)
	commitments = ListField(EmbeddedObjectListField(BigInt), is_hashed=False)
	challenge = EmbeddedObjectListField(BigInt, is_hashed=False)
	response = ListField(EmbeddedObjectListField(MixChallengeResponse), is_hashed=False)
	
	def compute_challenge(self, question_num):
		if self._instance[1] % 2 == 1:
			return self.recurse_parents(Election).mixing_trustees[self._instance[1] - 1].compute_challenge(question_num)
		
		sha = SHA256()
		trustees = self.recurse_parents(Election).mixing_trustees
		for i in range(len(trustees)):
			sha.update_text(EosObject.to_json(MixingTrustee._fields['mixed_questions'].element_field.serialise(trustees[i].mixed_questions[question_num])))
		for i in range(self._instance[1]):
			sha.update_text(EosObject.to_json(MixingTrustee._fields['response'].element_field.serialise(trustees[i].response[question_num])))
		return sha.hash_as_bigint()
	
	def get_input_answers(self, question_num):
		if self._instance[1] > 0:
			# Use the previous mixnet's output
			return self.recurse_parents(Election).mixing_trustees[self._instance[1] - 1].mixed_questions[question_num]
		else:
			# Use the raw ballots from voters
			orig_answers = []
			for voter in self.recurse_parents(Election).voters:
				if len(voter.votes) > 0:
					vote = voter.votes[-1]
					ballot = vote.ballot
					orig_answers.append(ballot.encrypted_answers[question_num])
			return orig_answers
	
	def verify(self, question_num):
		# Verify challenge
		challenge = self.compute_challenge(question_num)
		if challenge != self.challenge[question_num]:
			raise Exception('Invalid challenge')
		
		orig_answers = self.get_input_answers(question_num)
		
		# Prepare challenge bits
		challenge_bs = InfiniteHashBitStream(challenge)
		
		# Check each challenge response
		for k in range(len(self.mixed_questions[question_num])):
			response = self.response[question_num][k]
			
			challenge_bit = challenge_bs.read(1)
			should_reveal = ((self._instance[1] % 2) == (challenge_bit % 2))
			if should_reveal:
				if response is None:
					raise Exception('Response inconsistent with challenge')
				
				# Check the commitment matches
				if self.commitments[question_num][k] != SHA256().update_obj(response).hash_as_bigint():
					raise Exception('Invalid commitment')
				
				# Check the correct challenge/response pair
				if response.challenge_index != k:
					raise Exception('Invalid response')
				
				if self._instance[1] % 2 == 0:
					idx_left = response.challenge_index
					idx_right = response.response_index
				else:
					idx_right = response.challenge_index
					idx_left = response.response_index
				
				# Check the shuffle
				claimed_blocks = self.mixed_questions[question_num][idx_right].blocks
				for k in range(len(orig_answers[idx_left].blocks)):
					reencrypted_block, _ = orig_answers[idx_left].blocks[k].reencrypt(response.reenc[k])
					if claimed_blocks[k].gamma != reencrypted_block.gamma:
						raise Exception('Reencryption not consistent with challenge response')
					if claimed_blocks[k].delta != reencrypted_block.delta:
						raise Exception('Reencryption not consistent with challenge response')
			else:
				if response is not None:
					raise Exception('Response inconsistent with challenge')
		
		# Check the responses are consistent with a permutation
		challenge_indexes = []
		response_indexes = []
		for response in self.response[question_num]:
			if response is None:
				continue
			
			if response.challenge_index in challenge_indexes:
				raise Exception('Response not consistent with a permutation')
			if response.response_index in response_indexes:
				raise Exception('Response not consistent with a permutation')
			challenge_indexes.append(response.challenge_index)
			response_indexes.append(response.response_index)
		
		# Check the outputs are all different
		blocks = []
		for output in self.mixed_questions[question_num]:
			for block in output.blocks:
				block = (str(block.gamma), str(block.delta))
				if block in blocks:
					raise Exception('Duplicate ciphertexts in output')
				blocks.append(block)
	
	def mix_votes(self, question=0):
		return False
	def prove_mixes(self, question=0):
		return False

class InternalMixingTrustee(MixingTrustee):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.mixnets = []
	
	def mix_votes(self, question=0):
		__pragma__('skip')
		from eos.psr.mixnet import RPCMixnet
		__pragma__('noskip')
		
		election = self.recurse_parents('eos.base.election.Election')
		index = self._instance[1]
		
		self.mixnets.append(RPCMixnet(index))
		if index > 0:
			orig_answers = election.mixing_trustees[index - 1].mixed_questions[question]
		else:
			orig_answers = []
			for voter in election.voters:
				if len(voter.votes) > 0:
					ballot = voter.votes[-1].ballot
					orig_answers.append(ballot.encrypted_answers[question])
		shuffled_answers, commitments = self.mixnets[question].shuffle(orig_answers)
		self.mixed_questions.append(EosList(shuffled_answers))
		self.commitments.append(EosList(commitments))
		
		return True
	
	def prove_mixes(self, question=0):
		election = self.recurse_parents('eos.base.election.Election')
		index = self._instance[1]
		
		self.challenge.append(self.compute_challenge(question))
		challenge_bs = InfiniteHashBitStream(self.challenge[question])
		
		self.response.append(EosList())
		
		for k in range(len(self.mixed_questions[question])):
			challenge_bit = challenge_bs.read(1)
			should_reveal = ((index % 2) == (challenge_bit % 2))
			if should_reveal:
				response = self.mixnets[question].challenge(k)
				self.response[question].append(response)
			else:
				self.response[question].append(None)
		
		return True

class PSRElection(Election):
	_db_name = Election._name
	
	sk = EmbeddedObjectField(SEGPrivateKey, is_protected=True) # TODO: Threshold
	
	public_key = EmbeddedObjectField(SEGPublicKey)
	mixing_trustees = EmbeddedObjectListField()
