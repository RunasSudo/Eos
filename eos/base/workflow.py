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

class WorkflowTask(EmbeddedObject):
	class Status:
		UNKNOWN = 0
		NOT_READY = 10
		READY = 20
		ENTERED = 30
		#COMPLETE = 40
		EXITED = 50
	
	depends_on = []
	provides = []
	
	status = IntField(default=0, is_hashed=False)
	exited_at = DateTimeField(is_hashed=False)
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
	
	def post_init(self):
		super().post_init()
		
		self.workflow = self.recurse_parents(Workflow)
		
		if self.status == WorkflowTask.Status.UNKNOWN:
			self.status = WorkflowTask.Status.READY if self.are_dependencies_met() else WorkflowTask.Status.NOT_READY
		
		self.listeners = {
			'enter': [],
			'exit': []
		}
		
		# Helpers
		
		def on_dependency_exit():
			self.status = WorkflowTask.Status.READY if self.are_dependencies_met() else WorkflowTask.Status.NOT_READY
		for depends_on_desc in self.depends_on:
			for depends_on_task in self.workflow.get_tasks(depends_on_desc):
				depends_on_task.listeners['exit'].append(on_dependency_exit)
	
	def are_dependencies_met(self):
		for depends_on_desc in self.depends_on:
			for depends_on_task in self.workflow.get_tasks(depends_on_desc):
				if depends_on_task.status is not WorkflowTask.Status.EXITED:
					return False
		return True
	
	@classmethod
	def satisfies(cls, descriptor):
		return cls._name == descriptor or descriptor in cls.provides or (descriptor in EosObject.objects and issubclass(cls, EosObject.objects[descriptor]))
	
	def on_enter(self):
		self.exit()
	
	def enter(self):
		if self.status is not WorkflowTask.Status.READY:
			raise Exception('Attempted to enter a task when not ready')
		
		self.status = WorkflowTask.Status.ENTERED
		self.fire_event('enter')
		self.on_enter()
	
	def fire_event(self, event):
		for listener in self.listeners[event]:
			listener()
	
	def on_exit(self):
		self.exited_at = DateTimeField.now()
	
	def exit(self):
		if self.status is not WorkflowTask.Status.ENTERED:
			raise Exception('Attempted to exit a task when not entered')
		
		self.status = WorkflowTask.Status.EXITED
		self.fire_event('exit')
		self.on_exit()

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

# Concrete tasks
# ==============

class TaskConfigureElection(WorkflowTask):
	label = 'Configure the election and freeze the election'
	
	#def on_enter(self):
	#	self.status = WorkflowTask.Status.COMPLETE

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
			election.results.append(EosObject.objects['eos.base.election.RawResult']())
		
		for voter in election.voters:
			if len(voter.votes) > 0:
				vote = voter.votes[-1]
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
