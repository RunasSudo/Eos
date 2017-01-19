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
import eos_core.objects
import eos_basic.workflow

if eos_core.is_python:
	__pragma__ = lambda x: None
	__pragma__('skip')
	
	import django.core.exceptions
	import django.db.models
	import django.utils.timezone
	
	import datetime
	import uuid
	
	class EosDictObjectModelType(eos_core.objects.EosDictObjectType, django.db.models.base.ModelBase):
		def __new__(meta, name, bases, attrs):
			#import pdb; pdb.set_trace()
			meta, name, bases, attrs = eos_core.objects.EosDictObjectType._before_new(meta, name, bases, attrs)
			cls = django.db.models.base.ModelBase.__new__(meta, name, bases, attrs)
			cls = eos_core.objects.EosObjectType._after_new(cls, meta, name, bases, attrs)
			return cls
	
	class EosDictObjectModel(django.db.models.Model, eos_core.objects.EosDictObject, metaclass=EosDictObjectModelType):
		class Meta:
			abstract = True
		class EosMeta:
			abstract = True
		
		def __init__(self, *args, **kwargs):
			django.db.models.Model.__init__(self, *args, **kwargs)
	
	__pragma__('noskip')
else:
	EosDictObjectModelType = eos_core.objects.EosDictObjectType
	EosDictObjectModel = eos_core.objects.EosDictObject


class Question(eos_core.objects.EosObject):
	class EosMeta:
		abstract = True

class VoterEligibility(eos_core.objects.EosObject):
	class EosMeta:
		abstract = True

class Workflow(EosDictObjectModel):
	class EosMeta:
		eos_name = 'eos_core.models.Workflow'
		eos_fields = [
			eos_core.objects.EosField(eos_core.objects.uuid, 'id', primary_key=True, editable=False),
			eos_core.objects.EosField(str, 'workflow_name', max_length=100),
			eos_core.objects.EosField(list, 'tasks'), # [eos_core.workflow.WorkflowTask]
		]
	
	def __str__(self):
		return self.workflow_name
	
	def clean(self):
		for i, task in enumerate(self.tasks):
			for depends in task.workflow_depends:
				if self.get_task(depends, self.tasks[:i]) is None:
					raise django.core.exceptions.ValidationError({'tasks': '{} depends on {}'.format(eos_core.objects.get_full_name(task), depends)})
	
	def get_task(self, name, tasks=None):
		if tasks is None:
			tasks = self.tasks
		
		for task in tasks:
			if eos_core.objects.get_full_name(task) == name:
				return task
			if name in task.workflow_provides:
				return task
		return None

class Election(EosDictObjectModel):
	class EosMeta:
		eos_name = 'eos_core.models.Election'
		eos_fields = [
			eos_core.objects.EosField(eos_core.objects.uuid, 'id', primary_key=True, editable=False),
			eos_core.objects.EosField(str, 'election_name', max_length=100),
			eos_core.objects.EosField(Workflow, 'workflow', on_delete='PROTECT'),
			
			eos_core.objects.EosField(list, 'questions'), # [eos_core.models.Question]
			eos_core.objects.EosField(eos_core.objects.EosObject, 'voter_eligibility'), # eos_core.models.VoterEligibility
			
			eos_core.objects.EosField(eos_core.objects.datetime, 'voting_opens_at', nullable=True),
			eos_core.objects.EosField(eos_core.objects.datetime, 'voting_closes_at', nullable=True),
			
			eos_core.objects.EosField(eos_core.objects.datetime, 'frozen_at', nullable=True),
			
			eos_core.objects.EosField(eos_core.objects.datetime, 'voting_extended_until', nullable=True, hashed=False),
			eos_core.objects.EosField(eos_core.objects.datetime, 'voting_opened_at', nullable=True, hashed=False),
			eos_core.objects.EosField(eos_core.objects.datetime, 'voting_closed_at', nullable=True, hashed=False),
			eos_core.objects.EosField(eos_core.objects.datetime, 'result_released_at', nullable=True, hashed=False),
		]
	
	def __str__(self):
		return self.election_name
	
	@property
	def voting_has_opened(self):
		if not self.frozen_at:
			return False
		
		# Voting opened when manually opened, or when originally scheduled to open
		voting_opened_at = self.voting_opened_at if self.voting_opened_at else self.voting_opens_at
		
		if voting_opened_at:
			return django.utils.timezone.now() >= voting_opened_at
		return False
	
	@property
	def voting_has_closed(self):
		if not self.frozen_at:
			return False
		
		# Voting closed when manually closed, or when extension of voting expired, or when originally scheduled to close
		voting_closed_at = self.voting_closed_at if self.voting_closed_at else self.voting_extended_until if self.voting_extended_until else self.voting_closes_at
		
		if voting_closed_at:
			return django.utils.timezone.now() >= voting_closed_at
		return False

class Voter(eos_core.objects.EosObject):
	class EosMeta:
		abstract = True

# Represents a vote in hashable form, which is likely but not necessarily encrypted
class EncryptedVote(eos_core.objects.EosObject):
	class EosMeta:
		abstract = True

class PlaintextVote(EncryptedVote, eos_core.objects.EosDictObject):
	class EosMeta:
		eos_name = 'eos_core.models.PlaintextVote'

class CastVote(EosDictObjectModel):
	class EosMeta:
		eos_name = 'eos_core.models.CastVote'
		eos_fields = [
			eos_core.objects.EosField(eos_core.objects.uuid, 'id', primary_key=True, editable=False),
			eos_core.objects.EosField(Election, 'election', on_delete='PROTECT'),
			eos_core.objects.EosField(eos_core.objects.EosObject, 'voter'), # eos_core.models.Voter
			# We store the EncryptedVote inside rather than alongside CastVote as EncryptedVote may be of many different types
			eos_core.objects.EosField(eos_core.objects.EosObject, 'encrypted_vote'), # eos_core.models.EncryptedVote
			eos_core.objects.EosField(eos_core.objects.datetime, 'vote_received_at'),
		]
	
	def abc(self):
		pass
