#   Eos - Verifiable elections
#   Copyright © 2017-2019  RunasSudo (Yingtong Li)
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

from eos.core.tasks import *
from eos.core.objects import *

import threading

class ThreadingRunStrategy(RunStrategy):
	def run(self, task):
		def _run():
			task.status = TaskStatus.PROCESSING
			task.started_at = DateTimeField.now()
			task.save()
			
			try:
				task._run()
				task.status = TaskStatus.COMPLETE
				task.completed_at = DateTimeField.now()
				task.save()
				
				task.complete()
			except Exception as e:
				task.status = TaskStatus.FAILED
				task.completed_at = DateTimeField.now()
				if is_python:
					#__pragma__('skip')
					import traceback
					#__pragma__('noskip')
					task.messages.append(traceback.format_exc())
				else:
					task.messages.append(repr(e))
				task.save()
				
				task.error()
		
		thread = threading.Thread(target=_run, args=())
		thread.start()
