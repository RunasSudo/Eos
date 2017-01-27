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

import eos_core.workflow
import eos_core.libobjects

if eos_core.is_python:
	__pragma__ = lambda x: None
	__pragma__('skip')
	import django.core.urlresolvers
	__pragma__('noskip')

class TaskSetTrustees(eos_core.workflow.NullAdminWorkflowTask):
	workflow_depends = ['eos_core.workflow.TaskSetElectionDetails']
	
	class EosMeta:
		eos_name = 'eos_stjjr.workflow.TaskSetTrustees'
	
	def task_name(self, workflow, election):
		return 'Direct election trustees to submit their details'
	
	def is_complete(self, workflow, election):
		return False
