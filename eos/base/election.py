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

from eos.core.objects import *
from eos.core.bigint import *
from eos.base.workflow import *

class Answer(EmbeddedObject):
	pass

class EncryptedAnswer(EmbeddedObject):
	pass

class NullEncryptedAnswer(EncryptedAnswer):
	answer = EmbeddedObjectField()
	
	def decrypt(self):
		return None, self.answer

class Ballot(EmbeddedObject):
	#_id = UUIDField()
	encrypted_answers = EmbeddedObjectListField()
	election_id = UUIDField()
	election_hash = StringField()
	
	answers = EmbeddedObjectListField(is_hashed=False) # Used for ballots to be audited
	
	def deaudit(self):
		encrypted_answers_deaudit = EosList()
		
		for encrypted_answer in self.encrypted_answers:
			encrypted_answers_deaudit.append(encrypted_answer.deaudit())
		
		return Ballot(encrypted_answers=encrypted_answers_deaudit, election_id=self.election_id, election_hash=self.election_hash)

class Vote(EmbeddedObject):
	_ver = StringField(default='0.4')
	
	ballot = EmbeddedObjectField()
	cast_at = DateTimeField()
	
	cast_ip = StringField(is_protected=True)
	cast_fingerprint = BlobField(is_protected=True)

class Voter(EmbeddedObject):
	_id = UUIDField()
	votes = EmbeddedObjectListField()

class User(EmbeddedObject):
	admins = []
	
	def matched_by(self, other):
		return self == other
	
	def is_admin(self):
		for admin in User.admins:
			if admin.matched_by(self):
				return True
		return False

def generate_password():
	if is_python:
		#__pragma__('skip')
		import random
		return ''.join(random.SystemRandom().choices('23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz', k=12))
		#__pragma__('noskip')
	else:
		return None

class EmailUser(User):
	name = StringField()
	email = StringField(is_protected=True)
	password = StringField(is_protected=True, default=generate_password)
	
	def matched_by(self, other):
		if not isinstance(other, EmailUser):
			return False
		return self.email.lower() == other.email.lower() and self.password == other.password
	
	def send_email(self, host, port, username, password, from_email, content):
		#__pragma__('skip')
		import smtplib
		#__pragma__('noskip')
		with smtplib.SMTP(host, port) as smtp:
			if username is not None:
				smtp.login(username, password)
			smtp.sendmail(from_email, [self.email], content)
	
	def email_password(self, host, port, username, password, from_email):
		self.send_email(host, port, username, password, from_email, 'Subject: Registered to vote in {1}\nFrom: {4}\nTo: {2}\n\nDear {0},\n\nYou are registered to vote in the election {1}. Your log in details are as follows:\n\nEmail: {2}\nPassword: {3}'.format(self.name, self.recurse_parents(Election).name, self.email, self.password, from_email))

class UserVoter(Voter):
	user = EmbeddedObjectField()
	
	@property
	def name(self):
		return self.user.name

class Question(EmbeddedObject):
	prompt = StringField()

class Result(EmbeddedObject):
	pass

class ListChoiceQuestion(Question):
	_ver = StringField(default='0.5')
	
	choices = EmbeddedObjectListField()
	min_choices = IntField()
	max_choices = IntField()
	randomise_choices = BooleanField(default=False)
	
	def pretty_answer(self, answer):
		if len(answer.choices) == 0:
			return '(blank votes)'
		flat_choices = self.flatten_choices()
		return ', '.join([flat_choices[choice].name for choice in answer.choices])
	
	def max_bits(self):
		answer = self.answer_type(choices=list(range(len(self.choices))))
		return len(EosObject.to_json(EosObject.serialise_and_wrap(answer))) * 8
	
	def flatten_choices(self):
		# Return a flat list of Choices, without Tickets
		flat_choices = []
		for choice in self.choices:
			if isinstance(choice, Ticket):
				for choice2 in choice.choices:
					flat_choices.append(choice2)
			else:
				flat_choices.append(choice)
		return flat_choices
	
	def randomised_choices(self):
		if not self.randomise_choices:
			return self.choices
		else:
			# Clone list
			output = EosList([x for x in self.choices])
			# Fisher-Yates shuffle
			i = len(output)
			while i != 0:
				rnd = BigInt.noncrypto_random(0, i - 1)
				rnd = rnd.__int__()
				i -= 1
				output[rnd], output[i] = output[i], output[rnd]
			return output

class ApprovalAnswer(Answer):
	choices = ListField(IntField())

class ApprovalQuestion(ListChoiceQuestion):
	answer_type = ApprovalAnswer

class PreferentialAnswer(Answer):
	choices = ListField(IntField())

class PreferentialQuestion(ListChoiceQuestion):
	answer_type = PreferentialAnswer

class Choice(EmbeddedObject):
	name = StringField()
	party = StringField(default=None)
	
	@property
	def party_or_ticket(self):
		if self.party is not None:
			return self.party
		else:
			ticket = self.recurse_parents(Ticket)
			if ticket:
				return ticket.name
		return None

class Ticket(EmbeddedObject):
	name = StringField()
	choices = EmbeddedObjectListField()

class RawResult(Result):
	plaintexts = ListField(EmbeddedObjectListField())
	answers = EmbeddedObjectListField()
	
	def count(self):
		combined = []
		for answer in self.answers:
			index = next((i for i, val in enumerate(combined) if val[0] == answer), None)
			if index is None:
				combined.append([answer, 1])
			else:
				combined[index][1] += 1
		combined.sort(key=lambda x: x[1], reverse=True)
		return combined

class Election(TopLevelObject):
	_id = UUIDField()
	workflow = EmbeddedObjectField(Workflow) # Once saved, we don't care what kind of workflow it is
	name = StringField()
	kind = StringField(default='election')
	voters = EmbeddedObjectListField(is_hashed=False)
	questions = EmbeddedObjectListField()
	results = EmbeddedObjectListField(is_hashed=False)
	
	def verify(self):
		#__pragma__('skip')
		from eos.core.hashing import SHA256
		#__pragma__('noskip')
		election_hash = SHA256().update_obj(self).hash_as_b64()
		
		for voter in self.voters:
			for vote in voter.votes:
				if vote.ballot.election_id != self._id:
					raise Exception('Invalid election ID on ballot')
				if vote.ballot.election_hash != election_hash:
					raise Exception('Invalid election hash on ballot')
