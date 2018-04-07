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

class TaskStatus(EosEnum):
	UNKNOWN = 0
	
	READY = 20
	PROCESSING = 30
	COMPLETE = 50
	
	FAILED = -10
	TIMEOUT = -20
	
	def is_error(self):
		return self.value < 0

class Task(TopLevelObject):
	label = 'Unknown task'
	
	_id = UUIDField()
	run_strategy = EmbeddedObjectField()
	
	run_at = DateTimeField()
	
	started_at = DateTimeField()
	completed_at = DateTimeField()
	
	status = EnumField(TaskStatus, default=TaskStatus.UNKNOWN)
	messages = ListField(StringField())
	
	def run(self):
		self.run_strategy.run(self)
	
	def _run(self):
		pass
	
	def complete(self):
		pass
	
	def error(self):
		pass

class DummyTask(Task):
	_db_name = Task._db_name
	label = 'A dummy task'
	
	def _run(self):
		if is_python:
			#__pragma__('skip')
			import time
			#__pragma__('noskip')
			time.sleep(15)

class RunStrategy(DocumentObject):
	def run(self, task):
		raise Exception('Not implemented')

class TaskScheduler:
	@staticmethod
	def pending_tasks():
		pending_tasks = []
		tasks = Task.get_all()
		
		for task in tasks:
			if task.status == TaskStatus.READY:
				pending_tasks.append(task)
		
		# Sort them to ensure we iterate over them in the correct order
		pending_tasks.sort(key=lambda task: task.run_at.timestamp() if task.run_at else 0)
		
		return pending_tasks
	
	@staticmethod
	def active_tasks():
		active_tasks = []
		tasks = Task.get_all()
		
		for task in tasks:
			if task.status == TaskStatus.PROCESSING:
				active_tasks.append(task)
		
		return active_tasks
	
	@staticmethod
	def completed_tasks(limit=None):
		completed_tasks = []
		tasks = Task.get_all()
		
		for task in tasks:
			if task.status == TaskStatus.COMPLETE or task.status.is_error():
				completed_tasks.append(task)
		
		if limit:
			completed_tasks.sort(key=lambda x: x.completed_at)
			completed_tasks = completed_tasks[-limit:]
		
		return completed_tasks
	
	@staticmethod
	def tick():
		for task in TaskScheduler.pending_tasks():
			if task.run_at and task.run_at < DateTimeField.now():
				task.run()
