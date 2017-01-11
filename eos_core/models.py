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

import eos_core.fields
import eos_basic.workflow

import django.core.exceptions
import django.db.models

class Workflow(django.db.models.Model):
	name = django.db.models.CharField(max_length=100)
	tasks = eos_core.fields.EosListField()
	
	def __str__(self):
		return self.name
	
	def clean(self):
		for i, task in enumerate(self.tasks):
			for depends in task.workflow_depends:
				if self.get_task(depends, self.tasks[:i]) is None:
					raise django.core.exceptions.ValidationError({'tasks': '{} depends on {}'.format(eos_core.objects.get_full_name(task), depends)})
	
	def get_task(self, name, tasks=None):
		if tasks is None:
			tasks = self.tasks
		
		for task in tasks:
			if eos_core.objects.get_full_name(task) == name:
				return task
			if name in task.workflow_provides:
				return task
		return None
