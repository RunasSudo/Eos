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

class Task(TopLevelObject):
	class Status:
		UNKNOWN = 0
		
		READY = 20
		PROCESSING = 30
		COMPLETE = 50
		
		FAILED = -10
		TIMEOUT = -20
	
	_id = UUIDField()
	status = IntField(default=0)
	run_strategy = EmbeddedObjectField()
	messages = ListField(StringField())
	
	def run(self):
		self.run_strategy.run(self)
	
	def _run(self):
		pass

class RunStrategy(DocumentObject):
	def run(self, task):
		raise Exception('Not implemented')

class DirectRunStrategy(RunStrategy):
	def run(self, task):
		task.status = Task.Status.PROCESSING
		task.save()
		
		try:
			task._run()
			task.status = Task.Status.COMPLETE
			task.save()
		except Exception as e:
			task.status = Task.Status.FAILED
			if is_python:
				#__pragma__('skip')
				import traceback
				#__pragma__('noskip')
				task.messages.append(traceback.format_exc())
			else:
				task.messages.append(repr(e))
			task.save()
