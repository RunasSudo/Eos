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

import eos_core
import eos_core.libobjects
import eos_core.objects
import eos_core.models

# A type of question which permits voters to place check marks against the names of a specified number of candidates
class ApprovalQuestion(eos_core.libobjects.EosDictObject, eos_core.objects.Question):
	class EosMeta:
		eos_name = 'eos_basic.objects.ApprovalQuestion'
		eos_fields = [
			eos_core.libobjects.EosField(str, 'title'),
			eos_core.libobjects.EosField(str, 'description'),
			eos_core.libobjects.EosField(list, 'choices', element_type=eos_core.libobjects.EosField(str)),
			eos_core.libobjects.EosField(int, 'max_choices'),
			eos_core.libobjects.EosField(int, 'min_choices')
		]

class ApprovalQuestionResult(eos_core.libobjects.EosDictObject):
	class EosMeta:
		eos_name = 'eos_basic.objects.ApprovalQuestionResult'
		eos_fields = [
			eos_core.libobjects.EosField(list, 'tally', element_type=eos_core.libobjects.EosField(int))
		]

# All registered users are eligible to vote in this election
class UnconditionalVoterEligibility(eos_core.objects.VoterEligibility, eos_core.libobjects.EosObject):
	class EosMeta:
		eos_name = 'eos_basic.objects.UnconditionalVoterEligibility'
	
	def serialise(self, hashed=False):
		return None
	
	@staticmethod
	def _deserialise(cls, value):
		return cls()

class DjangoAuthVoter(eos_core.objects.Voter):
	class EosMeta:
		eos_name = 'eos_basic.objects.DjangoAuthVoter'
	
	def __init__(self, auth_user_id=None):
		self.auth_user_id = auth_user_id
	
	def serialise(self, hashed=False):
		return self.auth_user_id
	
	@staticmethod
	def _deserialise(cls, value):
		return cls(auth_user_id=value)
	
	@property
	def name(self):
		if eos_core.is_python:
			__pragma__ = lambda x: None
			__pragma__('skip')
			import django.contrib.auth.models
			return django.contrib.auth.models.User.objects.get(id=self.auth_user_id).username
			__pragma__('noskip')
		else:
			return None
