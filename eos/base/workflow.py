#   Eos - Verifiable elections
#   Copyright © 2017-18  RunasSudo (Yingtong Li)
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
from eos.core.tasks import *

class WorkflowTaskStatus(EosEnum):
	UNKNOWN = 0
	NOT_READY = 10
	READY = 20
	ENTERED = 30
	#COMPLETE = 40
	EXITED = 50

class WorkflowTask(EmbeddedObject):
	depends_on = []
	provides = []
	
	status = EnumField(WorkflowTaskStatus, is_hashed=False)
	exited_at = DateTimeField(is_hashed=False)
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
	
	def post_init(self):
		super().post_init()
		
		self.workflow = self.recurse_parents(Workflow)
		
		if self.status == WorkflowTaskStatus.UNKNOWN:
			self.status = WorkflowTaskStatus.READY if self.are_dependencies_met() else WorkflowTaskStatus.NOT_READY
		
		self.listeners = {
			'enter': [],
			'exit': []
		}
		
		# Helpers
		
		def on_dependency_exit():
			self.status = WorkflowTaskStatus.READY if self.are_dependencies_met() else WorkflowTaskStatus.NOT_READY
		for depends_on_desc in self.depends_on:
			for depends_on_task in self.workflow.get_tasks(depends_on_desc):
				depends_on_task.listeners['exit'].append(on_dependency_exit)
	
	def are_dependencies_met(self):
		for depends_on_desc in self.depends_on:
			for depends_on_task in self.workflow.get_tasks(depends_on_desc):
				if depends_on_task.status is not WorkflowTaskStatus.EXITED:
					return False
		return True
	
	@classmethod
	def satisfies(cls, descriptor):
		return cls._name == descriptor or descriptor in cls.provides or (descriptor in EosObject.objects and issubclass(cls, EosObject.lookup(descriptor)))
	
	def on_enter(self):
		self.exit()
	
	def enter(self):
		if self.status is not WorkflowTaskStatus.READY:
			raise Exception('Attempted to enter a task when not ready')
		
		self.status = WorkflowTaskStatus.ENTERED
		self.fire_event('enter')
		self.on_enter()
	
	def fire_event(self, event):
		for listener in self.listeners[event]:
			listener()
	
	def on_exit(self):
		self.exited_at = DateTimeField.now()
	
	def exit(self):
		if self.status is not WorkflowTaskStatus.ENTERED:
			raise Exception('Attempted to exit a task when not entered')
		
		self.status = WorkflowTaskStatus.EXITED
		self.fire_event('exit')
		self.on_exit()
	
	def get_entry_task(self):
		election = self.recurse_parents('eos.base.election.Election')
		
		for task in WorkflowTaskEntryTask.get_all():
			if task.election_id == election._id and task.workflow_task == self._name:
				return task
		
		return None

class Workflow(EmbeddedObject):
	tasks = EmbeddedObjectListField()
	meta = {
		'abstract': True
	}
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
	
	def get_tasks(self, descriptor):
		#yield from (task for task in self.tasks if task.satisfies(descriptor))
		for task in self.tasks:
			if task.satisfies(descriptor):
				yield task
	
	def get_task(self, descriptor):
		try:
			return next(self.get_tasks(descriptor))
		except StopIteration:
			return None

class WorkflowTaskEntryTask(Task):
	election_id = UUIDField()
	workflow_task = StringField()
	
	def _run(self):
		election = EosObject.lookup('eos.base.election.Election').get_by_id(self.election_id)
		task = election.workflow.get_task(self.workflow_task)
		task.enter()
		election.save()
	
	@property
	def label(self):
		election = EosObject.lookup('eos.base.election.Election').get_by_id(self.election_id)
		task = election.workflow.get_task(self.workflow_task)
		return task.label + ' – ' + election.name

# Concrete tasks
# ==============

class TaskConfigureElection(WorkflowTask):
	label = 'Freeze the election'
	
	#def on_enter(self):
	#	self.status = WorkflowTaskStatus.COMPLETE

class TaskOpenVoting(WorkflowTask):
	label = 'Open voting'
	depends_on = ['eos.base.workflow.TaskConfigureElection']

class TaskCloseVoting(WorkflowTask):
	label = 'Close voting'
	depends_on = ['eos.base.workflow.TaskOpenVoting']

class TaskDecryptVotes(WorkflowTask):
	label = 'Decrypt the votes'
	depends_on = ['eos.base.workflow.TaskCloseVoting']
	
	def on_enter(self):
		election = self.recurse_parents('eos.base.election.Election')
		
		for _ in range(len(election.questions)):
			election.results.append(EosObject.lookup('eos.base.election.RawResult')())
		
		for voter in election.voters:
			if len(voter.votes.get_all()) > 0:
				vote = voter.votes.get_all()[-1]
				ballot = vote.ballot
				for q_num in range(len(ballot.encrypted_answers)):
					plaintexts, answer = ballot.encrypted_answers[q_num].decrypt()
					election.results[q_num].plaintexts.append(plaintexts)
					election.results[q_num].answers.append(answer)
		
		self.exit()

class TaskReleaseResults(WorkflowTask):
	label = 'Release the results'
	depends_on = ['eos.base.workflow.TaskDecryptVotes']

# Concrete workflows
# ==================

class WorkflowBase(Workflow):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		self.tasks.append(TaskConfigureElection())
		self.tasks.append(TaskOpenVoting())
		self.tasks.append(TaskCloseVoting())
		self.tasks.append(TaskDecryptVotes())
		self.tasks.append(TaskReleaseResults())
