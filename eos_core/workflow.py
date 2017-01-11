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

import eos_core.objects

workflow_tasks = {}

class WorkflowTaskType(eos_core.objects.EosDictObjectType):
	def __new__(cls, name, bases, attrs):
		instance = super().__new__(cls, name, bases, attrs)
		workflow_tasks[eos_core.objects.get_full_name(instance)] = instance
		return instance

class WorkflowTask(eos_core.objects.EosDictObject, metaclass=WorkflowTaskType):
	eos_fields = []
	workflow_provides = []
	workflow_depends = []
	#workflow_conflicts = []
	#workflow_after = []
	#workflow_before = []
	
	@staticmethod
	def get_all():
		import eos.settings
		import importlib
		for app in eos.settings.INSTALLED_APPS:
			try:
				importlib.import_module(app)
			except ImportError:
				pass
		return workflow_tasks
