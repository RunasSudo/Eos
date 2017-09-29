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

class BlockEncryptedAnswer(EncryptedAnswer):
	blocks = EmbeddedObjectListField()
	
	@classmethod
	def encrypt(cls, pk, obj):
		pt = EosObject.to_json(EosObject.serialise_and_wrap(obj))
		bs = BitStream()
		bs.write_string(pt)
		bs.multiple_of(pk.group.p.nbits() - 1, True)
		ct = bs.map(pk.encrypt, pk.group.p.nbits() - 1)
		
		return cls(blocks=ct)
	
	def decrypt(self, sk=None):
		if sk is None:
			sk = self.recurse_parents(PSRElection).sk
		
		bs = BitStream.unmap(self.blocks, sk.decrypt, sk.public_key.group.p.nbits() - 1)
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
	mixed_questions = ListField(EmbeddedObjectListField(BlockEncryptedAnswer))
	commitments = ListField(EmbeddedObjectListField(BigInt))
	challenge = EmbeddedObjectListField(BigInt)
	response = ListField(EmbeddedObjectListField(MixChallengeResponse))
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.mixnets = [] # TODO: Remove this stuff
	
	def compute_challenge(self, question_num):
		sha = SHA256()
		trustees = self.recurse_parents(Election).mixing_trustees
		for i in range(len(trustees)):
			sha.update_text(EosObject.to_json(MixingTrustee._fields['mixed_questions'].element_field.serialise(trustees[i].mixed_questions[question_num])))
		for i in range(self._instance[1]):
			sha.update_text(EosObject.to_json(MixingTrustee._fields['response'].element_field.serialise(trustees[i].response[question_num])))
		return sha

class PSRElection(Election):
	_db_name = Election._name
	
	sk = EmbeddedObjectField(SEGPrivateKey) # TODO: Threshold
	mixing_trustees = EmbeddedObjectListField(MixingTrustee)
