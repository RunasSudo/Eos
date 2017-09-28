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
	_id = UUIDField()
	encrypted_answers = EmbeddedObjectListField()

class Voter(EmbeddedObject):
	_id = UUIDField()
	ballots = EmbeddedObjectListField()

class Question(EmbeddedObject):
	prompt = StringField()

class Result(EmbeddedObject):
	pass

class ApprovalQuestion(Question):
	choices = ListField(StringField())

class ApprovalAnswer(Answer):
	choices = ListField(IntField())

class RawResult(Result):
	answers = EmbeddedObjectListField()

class Election(TopLevelObject):
	_id = UUIDField()
	workflow = EmbeddedObjectField(Workflow) # Once saved, we don't care what kind of workflow it is
	name = StringField()
	voters = EmbeddedObjectListField(hashed=False)
	questions = EmbeddedObjectListField()
	results = EmbeddedObjectListField(hashed=False)
