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

if eos_core.is_python:
	__pragma__ = lambda x: None
	__pragma__('skip')
	import django.core.urlresolvers
	__pragma__('noskip')

workflow_tasks = {}

class WorkflowTaskType(eos_core.libobjects.EosObjectType):
	def __new__(meta, name, bases, attrs):
		#cls = super().__new__(meta, name, bases, attrs)
		cls = eos_core.libobjects.EosObjectType.__new__(meta, name, bases, attrs)
		
		if not getattr(cls._eosmeta, 'abstract', False):
			workflow_tasks[eos_core.libobjects.get_full_name(cls)] = cls
		
		return cls

class WorkflowTask(eos_core.libobjects.EosObject, metaclass=WorkflowTaskType):
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
		return workflow_tasks
	
	def are_restrictions_met(self, workflow, election):
		for task in self.workflow_depends:
			if not workflow.get_task(task):
				return False
			if not workflow.get_task(task).is_complete(workflow, election):
				return False
		return True
	
	def is_pending(self, workflow, election):
		return self.are_restrictions_met(workflow, election) and not self.is_complete(workflow, election)

# A workflow task with no value
class NullWorkflowTask(WorkflowTask):
	class EosMeta:
		abstract = True
	
	def serialise(self, hashed=False):
		return None
	
	@staticmethod
	def _deserialise(cls, value):
		return cls()

# A workflow task whose associated URL is the election admin URL
class NullAdminWorkflowTask(NullWorkflowTask):
	class EosMeta:
		abstract = True
	
	def task_url(self, workflow, election):
		return django.core.urlresolvers.reverse('admin:eos_core_election_change', args=[election.id])

class TaskSetElectionDetails(NullAdminWorkflowTask):
	class EosMeta:
		eos_name = 'eos_core.workflow.TaskSetElectionDetails'
	
	def task_name(self, workflow, election):
		return 'Set election details and freeze election'
	
	def is_complete(self, workflow, election):
		return election.frozen_at is not None

class TaskOpenVoting(NullAdminWorkflowTask):
	workflow_depends = ['eos_core.workflow.TaskSetElectionDetails']
	
	class EosMeta:
		eos_name = 'eos_core.workflow.TaskOpenVoting'
	
	def task_name(self, workflow, election):
		return 'Open voting'
	
	def is_complete(self, workflow, election):
		return election.voting_has_opened

class TaskExtendVoting(NullAdminWorkflowTask):
	workflow_depends = ['eos_core.workflow.TaskSetElectionDetails']
	
	class EosMeta:
		eos_name = 'eos_core.workflow.TaskExtendVoting'
	
	def task_name(self, workflow, election):
		return 'Extend voting'
	
	def is_complete(self, workflow, election):
		# We can always keep extending voting
		return False
	
	def are_restrictions_met(self, workflow, election):
		if not NullAdminWorkflowTask.are_restrictions_met(self, workflow, election):
			return False
		# We cannot extend voting if we manually closed it
		return election.voting_closed_at is None

class TaskCloseVoting(NullAdminWorkflowTask):
	workflow_depends = ['eos_core.workflow.TaskOpenVoting']
	
	class EosMeta:
		eos_name = 'eos_core.workflow.TaskCloseVoting'
	
	def task_name(self, workflow, election):
		return 'Close voting'
	
	def is_complete(self, workflow, election):
		return election.voting_has_closed

class TaskComputeResult(NullWorkflowTask):
	workflow_depends = ['eos_core.workflow.TaskCloseVoting']
	
	class EosMeta:
		abstract = True
	
	def task_name(self, workflow, election):
		return 'Compute result'
	
	def task_url(self, workflow, election):
		return django.core.urlresolvers.reverse('election_compute_result', args=[election.id])

class TaskReleaseResult(NullAdminWorkflowTask):
	workflow_depends = ['eos_core.workflow.TaskComputeResult']
	
	class EosMeta:
		eos_name = 'eos_core.workflow.TaskReleaseResult'
	
	def task_name(self, workflow, election):
		return 'Release result'
	
	def is_complete(self, workflow, election):
		return election.result_released_at is not None
