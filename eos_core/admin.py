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
import django.core.exceptions
import django.forms
import django.utils.html
import django.utils.timezone

import datetime

class EosObjectWidget(django.contrib.admin.widgets.AdminTextareaWidget):
	def render(self, name, value, attrs=None):
		if not isinstance(value, str):
			value = eos_core.objects.to_json(eos_core.objects.EosObject.serialise_and_wrap(value, None))
		return super().render(name, value, attrs)

class EosObjectFormField(django.forms.CharField):
	def __init__(self, *args, **kwargs):
		if 'widget' not in kwargs:
			kwargs['widget'] = EosObjectWidget
		super().__init__(*args, **kwargs)
	
	def to_python(self, value):
		return eos_core.objects.EosObject.deserialise_and_unwrap(eos_core.objects.from_json(value), None)

class EosListWidget(django.contrib.admin.widgets.AdminTextareaWidget):
	def render(self, name, value, attrs=None):
		if not isinstance(value, str):
			value = eos_core.objects.to_json(eos_core.objects.EosObject.serialise_list(value, None))
		return super().render(name, value, attrs)

class EosListFormField(django.forms.CharField):
	def __init__(self, *args, **kwargs):
		if 'widget' not in kwargs:
			kwargs['widget'] = EosListWidget
		super().__init__(*args, **kwargs)
	
	def to_python(self, value):
		return eos_core.objects.EosObject.deserialise_list(eos_core.objects.from_json(value), None)

class WorkflowTasksWidget(EosListWidget):
	def render(self, name, value, attrs=None):
		if not isinstance(value, str):
			value = eos_core.objects.to_json(eos_core.objects.EosObject.serialise_list(value, None))
		tasks_field = super().render(name, value, attrs)
		# Oh my...
		# TODO: Use a template or something
		return '<div style="float: left;"><div>' + tasks_field + '</div><div>' + django.forms.Select(choices=[(workflow_task, workflow_task) for workflow_task in eos_core.workflow.WorkflowTask.get_all()]).render(name + '_add_type', value) + ' <a href="#" class="addlink" onclick="var tasks_field = document.getElementsByName(\'' + name + '\')[0]; var tasks_field_list = JSON.parse(tasks_field.value); tasks_field_list.push({\'type\': document.getElementsByName(\'' + name + '_add_type\')[0].value, \'value\': null}); tasks_field.value = JSON.stringify(tasks_field_list); return false;">Add</a></div></div>'

class WorkflowAdminForm(django.forms.ModelForm):
	tasks = EosListFormField(widget=WorkflowTasksWidget)
	
	def clean_tasks(self):
		data = self.cleaned_data['tasks']
		if not isinstance(eos_core.objects.EosObject.deserialise_list(eos_core.objects.from_json(data), None), list):
			raise django.forms.ValidationError('This field must be a list.')
		return data

class WorkflowAdmin(django.contrib.admin.ModelAdmin):
	form = WorkflowAdminForm

class LinkButtonWidget(django.forms.HiddenInput):
	is_hidden = False
	
	def render(self, name, value, attrs=None):
		return super().render(name, value, attrs) + '<input value="Save and freeze" type="button" onclick="document.getElementsByName(\'' + name + '\')[0].value = \'freeze\'; document.getElementsByName(\'_continue\')[0].click();">'

class ElectionAdminForm(django.forms.ModelForm):
	voting_starts_at = django.forms.SplitDateTimeField(required=False, widget=django.contrib.admin.widgets.AdminSplitDateTime)
	voting_ends_at = django.forms.SplitDateTimeField(required=False, widget=django.contrib.admin.widgets.AdminSplitDateTime)
	questions = EosListFormField()
	voter_eligibility = EosObjectFormField()
	freeze = django.forms.BooleanField(required=False, label='', widget=LinkButtonWidget)
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
	
	def clean_freeze(self):
		if self.cleaned_data['freeze']:
			if self.instance.frozen_at:
				raise django.core.exceptions.ValidationError('Attempted to freeze an already-frozen election')
			self.instance.frozen_at = django.utils.timezone.now()

class ElectionAdmin(django.contrib.admin.ModelAdmin):
	form = ElectionAdminForm
	
	#class Media:
	#	css = {
	#		'all': ['eos_core_admin/css/icons.css']
	#	}
	
	def get_fieldsets(self, request, obj=None):
		fields_general = ['name', 'workflow'] if (obj is None or not obj.frozen_at) else []
		fields_schedule = ['voting_starts_at', 'voting_ends_at'] if (obj is None or not obj.frozen_at) else ['voting_extended_until'] if not obj.voting_ended_at else []
		fields_questions = ['questions'] if (obj is None or not obj.frozen_at) else []
		fields_voters = ['voter_eligibility'] if (obj is None or not obj.frozen_at) else []
		fields_freeze = ['freeze'] if (obj is None or not obj.frozen_at) else []
		
		return (
			([(None, {'fields': fields_general})] if fields_general else []) +
			([('Schedule', {'fields': fields_schedule})] if fields_schedule else []) +
			([('Questions', {'fields': fields_questions})] if fields_questions else []) +
			([('Voters', {'fields': fields_voters})] if fields_voters else []) +
			([('Freeze Election', {'fields': fields_freeze})] if fields_freeze else [])
		)

django.contrib.admin.site.register(eos_core.models.Workflow, WorkflowAdmin)
django.contrib.admin.site.register(eos_core.models.Election, ElectionAdmin)
