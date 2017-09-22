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
		NOT_READY = 10
		READY = 20
		#ENTERED = 30
		#COMPLETE = 40
		EXITED = 50
	
	depends_on = []
	provides = []
	
	status = IntField()
	
	def __init__(self, workflow=None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		self.workflow = workflow
		
		if self.workflow is None:
			self.workflow = self._instance
		
		self.status = WorkflowTask.Status.READY if self.are_dependencies_met() else WorkflowTask.Status.NOT_READY
		
		self.listeners = {
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
		return cls._name == descriptor or descriptor in cls.provides
	
	def fire_event(self, event):
		for listener in self.listeners[event]:
			listener()
	
	def exit(self):
		if self.status is not WorkflowTask.Status.READY:
			raise Exception()
		
		self.status = WorkflowTask.Status.EXITED
		self.fire_event('exit')

class Workflow(EmbeddedObject):
	tasks = EmbeddedObjectListField(WorkflowTask)
	meta = {
		'abstract': True
	}
	
	def __init__(self, election=None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.election = election if election else self._instance
	
	def get_tasks(self, descriptor):
		yield from (task for task in self.tasks if task.satisfies(descriptor))
	
	def get_task(self, descriptor):
		try:
			return next(self.get_tasks(descriptor))
		except StopIteration:
			return None

# Concrete tasks
# ==============

class TaskConfigureElection(WorkflowTask):
	#def on_enter(self):
	#	self.status = WorkflowTask.Status.COMPLETE
	pass

class TaskOpenVoting(WorkflowTask):
	depends_on = ['eos.base.workflow.TaskConfigureElection']

# Concrete workflows
# ==================

class WorkflowBase(Workflow):
	def __init__(self, election=None, *args, **kwargs):
		super().__init__(election, *args, **kwargs)
		
		self.tasks.append(TaskConfigureElection(self))
		self.tasks.append(TaskOpenVoting(self))
