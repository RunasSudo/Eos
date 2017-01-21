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

import eos_core.libobjects
import eos_core.workflow

if eos_core.is_python:
	__pragma__ = lambda x: None
	__pragma__('skip')
	import django.core.urlresolvers
	__pragma__('noskip')

class EosDictObjectWorkflowTaskType(eos_core.libobjects.EosDictObjectType, eos_core.workflow.WorkflowTaskType):
	def __new__(meta, name, bases, attrs):
		meta, name, bases, attrs = eos_core.libobjects.EosDictObjectType._before_new(meta, name, bases, attrs)
		cls = eos_core.workflow.WorkflowTaskType.__new__(meta, name, bases, attrs)
		cls = eos_core.libobjects.EosObjectType._after_new(cls, meta, name, bases, attrs)
		return cls

class EosDictObjectWorkflowTask(eos_core.workflow.WorkflowTask, eos_core.libobjects.EosDictObject, metaclass=EosDictObjectWorkflowTaskType):
	class EosMeta:
		abstract = True
	
	def __init__(self, *args, **kwargs):
		eos_core.workflow.WorkflowTask.__init__(self)
		eos_core.libobjects.EosDictObject.__init__(self, *args, **kwargs)

class TaskReceiveVotes(EosDictObjectWorkflowTask):
	workflow_provides = ['eos_core.workflow.TaskReceiveVotes']
	workflow_depends = ['eos_core.workflow.TaskOpenVoting']
	
	class EosMeta:
		eos_name = 'eos_basic.workflow.TaskReceiveVotes'
		eos_fields = [
			eos_core.libobjects.EosField(list, 'booth_tasks') # [eos_basic.workflow.BoothTask]
		]
	
	def task_name(self, workflow, election):
		return 'Cast votes'
	
	def task_url(self, workflow, election):
		return django.core.urlresolvers.reverse('election_voting_booth', args=[election.id])
	
	def is_complete(self, workflow, election):
		# We are never finished receiving votes
		return False
	
	def are_restrictions_met(self, workflow, election):
		if not super().are_restrictions_met(workflow, election):
			return False
		return election.voting_has_opened and not election.voting_has_closed

booth_tasks = {}

class BoothTaskType(eos_core.libobjects.EosObjectType):
	def __new__(meta, name, bases, attrs):
		#cls = super().__new__(meta, name, bases, attrs)
		cls = eos_core.libobjects.EosObjectType.__new__(meta, name, bases, attrs)
		
		if not getattr(cls._eosmeta, 'abstract', False):
			booth_tasks[eos_core.libobjects.get_full_name(cls)] = cls
		
		return cls

class BoothTask(eos_core.libobjects.EosObject, metaclass=BoothTaskType):
	workflow_provides = []
	workflow_depends = []
	#workflow_conflicts = []
	#workflow_after = []
	workflow_before = []
	
	class EosMeta:
		abstract = True
	
	@staticmethod
	def get_all():
		if eos_core.is_python:
			__pragma__ = lambda x: None
			__pragma__('skip')
			import eos.settings
			import importlib
			for app in eos.settings.INSTALLED_APPS:
				try:
					importlib.import_module(app + '.workflow')
				except ImportError:
					pass
			__pragma__('noskip')
		return booth_tasks

class NullBoothTask(BoothTask):
	class EosMeta:
		abstract = True
	
	def serialise(self, hashed=False):
		return None
	
	@staticmethod
	def _deserialise(cls, value):
		return cls()

class BoothTaskWelcome(NullBoothTask):
	class EosMeta:
		eos_name = 'eos_basic.workflow.BoothTaskWelcome'

class BoothTaskMakeSelections(NullBoothTask):
	class EosMeta:
		eos_name = 'eos_basic.workflow.BoothTaskMakeSelections'

class BoothTaskReviewSelections(NullBoothTask):
	class EosMeta:
		eos_name = 'eos_basic.workflow.BoothTaskReviewSelections'

class BoothTaskEncryptBallot(NullBoothTask):
	class EosMeta:
		eos_name = 'eos_basic.workflow.BoothTaskEncryptBallot'

class BoothTaskAuditBallot(NullBoothTask):
	class EosMeta:
		eos_name = 'eos_basic.workflow.BoothTaskAuditBallot'

class BoothTaskCastVote(NullBoothTask):
	class EosMeta:
		eos_name = 'eos_basic.workflow.BoothTaskCastVote'
