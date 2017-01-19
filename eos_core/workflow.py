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
	#workflow_before = []
	
	class EosMeta:
		abstract = True
	
	@staticmethod
	def get_all():
		#import eos.settings
		#import importlib
		#for app in eos.settings.INSTALLED_APPS:
		#	try:
		#		importlib.import_module(app + '.workflow')
		#	except ImportError:
		#		pass
		return workflow_tasks

class CoreWorkflowTask(WorkflowTask):
	class EosMeta:
		eos_name = 'eos_core.workflow.CoreWorkflowTask'
	
	def __init__(self, name=None):
		self.name = name
	
	@property
	def workflow_depends(self):
		return ['eos_basic.workflow.TaskSetElectionDetails']
	
	def serialise(self, hashed=False):
		return self.name
	
	@staticmethod
	def _deserialise(cls, value):
		return cls(name=value)
