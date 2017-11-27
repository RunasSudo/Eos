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
from eos.base.workflow import *

class Answer(EmbeddedObject):
	pass

class EncryptedAnswer(EmbeddedObject):
	pass

class NullEncryptedAnswer(EncryptedAnswer):
	answer = EmbeddedObjectField()
	
	def decrypt(self):
		return self.answer

class Ballot(EmbeddedObject):
	#_id = UUIDField()
	encrypted_answers = EmbeddedObjectListField()
	election_id = UUIDField()
	election_hash = StringField()

class Vote(EmbeddedObject):
	ballot = EmbeddedObjectField()
	cast_at = DateTimeField()

class Voter(EmbeddedObject):
	_id = UUIDField()
	votes = EmbeddedObjectListField()

class User(EmbeddedObject):
	pass

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
		return self.email == other.email and self.password == other.password
	
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

class ApprovalQuestion(Question):
	choices = ListField(StringField())
	min_choices = IntField()
	max_choices = IntField()
	
	def pretty_answer(self, answer):
		return ', '.join([self.choices[choice] for choice in answer.choices])

class ApprovalAnswer(Answer):
	choices = ListField(IntField())

class PreferentialQuestion(Question):
	choices = ListField(StringField())
	min_choices = IntField()
	max_choices = IntField()
	
	def pretty_answer(self, answer):
		return ', '.join([self.choices[choice] for choice in answer.choices])

class PreferentialAnswer(Answer):
	choices = ListField(IntField())

class RawResult(Result):
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
	voters = EmbeddedObjectListField(is_hashed=False)
	questions = EmbeddedObjectListField()
	results = EmbeddedObjectListField(is_hashed=False)
