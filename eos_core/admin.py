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

import eos_core.models
import eos_core.objects

import django.contrib.admin
import django.forms
import django.utils.html

import json

class WorkflowTasksWidget(django.forms.Textarea):
	def render(self, name, value, attrs=None):
		if not isinstance(value, str):
			value = json.dumps(eos_core.objects.EosObject.serialise_list(value, None))
		tasks_field = super().render(name, value, attrs)
		# Oh my...
		# TODO: Use a template or something
		return '<div style="float: left;"><div>' + tasks_field + '</div><div>' + django.forms.Select(choices=[(workflow_task, workflow_task) for workflow_task in eos_core.workflow.WorkflowTask.get_all()]).render(name + '_add_type', value) + ' <a href="#" class="addlink" onclick="var tasks_field = document.getElementsByName(\'' + name + '\')[0]; var tasks_field_list = JSON.parse(tasks_field.value); tasks_field_list.push({\'type\': document.getElementsByName(\'' + name + '_add_type\')[0].value, \'value\': {}}); tasks_field.value = JSON.stringify(tasks_field_list); return false;">Add</a></div></div>'

class WorkflowAdminForm(django.forms.ModelForm):
	tasks = django.forms.CharField(widget=WorkflowTasksWidget)
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
	
	def clean_tasks(self):
		data = self.cleaned_data['tasks']
		if not isinstance(eos_core.objects.EosObject.deserialise_list(json.loads(data), None), list):
			raise django.forms.ValidationError('This field must be a list.')
		return data

class WorkflowAdmin(django.contrib.admin.ModelAdmin):
	form = WorkflowAdminForm

django.contrib.admin.site.register(eos_core.models.Workflow, WorkflowAdmin)
