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
import eos_core.libobjects

import django.contrib.admin
import django.core.exceptions
import django.core.urlresolvers
import django.forms
import django.utils.html
import django.utils.safestring
import django.utils.timezone

import datetime

class EosObjectFormField(django.forms.CharField):
	def __init__(self, *args, **kwargs):
		if 'widget' not in kwargs:
			kwargs['widget'] = django.contrib.admin.widgets.AdminTextareaWidget
		super().__init__(*args, **kwargs)
	
	def to_python(self, value):
		return eos_core.libobjects.EosObject.deserialise_and_unwrap(eos_core.libobjects.from_json(value), None)

class EosListWidget(django.contrib.admin.widgets.AdminTextareaWidget):
	def render(self, name, value, attrs=None):
		if not isinstance(value, str):
			value = eos_core.libobjects.to_json(eos_core.libobjects.EosObject.serialise_list(value, None))
		return super().render(name, value, attrs)

class EosListFormField(django.forms.CharField):
	def __init__(self, *args, **kwargs):
		if 'widget' not in kwargs:
			kwargs['widget'] = EosListWidget
		super().__init__(*args, **kwargs)
	
	def to_python(self, value):
		return eos_core.libobjects.EosObject.deserialise_list(eos_core.libobjects.from_json(value), None)

class WorkflowTasksWidget(EosListWidget):
	def render(self, name, value, attrs=None):
		if not isinstance(value, str):
			value = eos_core.libobjects.to_json(eos_core.libobjects.EosObject.serialise_list(value, None))
		tasks_field = super().render(name, value, attrs)
		# Oh my...
		# TODO: Use a template or something
		return '<div style="float: left;"><div>' + tasks_field + '</div><div>' + django.forms.Select(choices=[(workflow_task, workflow_task) for workflow_task in eos_core.workflow.WorkflowTask.get_all()]).render(name + '_add_type', value) + ' <a href="#" class="addlink" onclick="var tasks_field = document.getElementsByName(\'' + name + '\')[0]; var tasks_field_list = JSON.parse(tasks_field.value); tasks_field_list.push({\'type\': document.getElementsByName(\'' + name + '_add_type\')[0].value, \'value\': null}); tasks_field.value = JSON.stringify(tasks_field_list); return false;">Add</a></div></div>'

class WorkflowAdminForm(django.forms.ModelForm):
	tasks = EosListFormField(widget=WorkflowTasksWidget)
	
	def clean_tasks(self):
		data = self.cleaned_data['tasks']
		#import pdb; pdb.set_trace()
		#if not isinstance(eos_core.libobjects.EosObject.deserialise_list(eos_core.libobjects.from_json(data), None), list):
		if not isinstance(data, list):
			raise django.forms.ValidationError('This field must be a list.')
		return data

class WorkflowAdmin(django.contrib.admin.ModelAdmin):
	form = WorkflowAdminForm

class SubmitAndActionButtonWidget(django.forms.HiddenInput):
	is_hidden = False
	
	def render(self, name, value, attrs=None):
		return super().render(name, value, attrs) + '<input value="' + self.button_label + '" type="button" onclick="document.getElementsByName(\'' + name + '\')[0].value = \'' + name + '\'; document.getElementsByName(\'_continue\')[0].click();">'

class SubmitAndActionButtonField(django.forms.CharField):
	def __init__(self, *args, **kwargs):
		if 'widget' not in kwargs:
			kwargs['widget'] = SubmitAndActionButtonWidget
		
		button_label = kwargs.pop('button_label')
		
		super().__init__(*args, **kwargs)
		
		self.widget.button_label = button_label

class ElectionAdminForm(django.forms.ModelForm):
	voting_opens_at = django.forms.SplitDateTimeField(required=False, widget=django.contrib.admin.widgets.AdminSplitDateTime)
	voting_closes_at = django.forms.SplitDateTimeField(required=False, widget=django.contrib.admin.widgets.AdminSplitDateTime)
	questions = EosListFormField()
	voter_eligibility = EosObjectFormField()
	
	freeze = SubmitAndActionButtonField(required=False, label='', button_label='Save and freeze')
	open_voting = SubmitAndActionButtonField(required=False, label='', button_label='Save and open voting')
	close_voting = SubmitAndActionButtonField(required=False, label='', button_label='Save and close voting')
	release_result = SubmitAndActionButtonField(required=False, label='', button_label='Save and release result')
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
	
	def clean_freeze(self):
		if self.cleaned_data['freeze']:
			if self.instance.frozen_at:
				raise django.core.exceptions.ValidationError('Attempted to freeze an already-frozen election')
			self.instance.frozen_at = django.utils.timezone.now()
	
	def clean_open_voting(self):
		if self.cleaned_data['open_voting']:
			if self.instance.voting_has_opened:
				raise django.core.exceptions.ValidationError('Attempted to open an already-open election')
			self.instance.voting_opened_at = django.utils.timezone.now()
	
	def clean_close_voting(self):
		if self.cleaned_data['close_voting']:
			if self.instance.voting_has_closed:
				raise django.core.exceptions.ValidationError('Attempted to close an already-closed election')
			self.instance.voting_closed_at = django.utils.timezone.now()
	
	def clean_release_result(self):
		if self.cleaned_data['release_result']:
			if self.instance.result_released_at:
				raise django.core.exceptions.ValidationError('Attempted to release an already-released result')
			self.instance.result_released_at = django.utils.timezone.now()

class ElectionAdmin(django.contrib.admin.ModelAdmin):
	form = ElectionAdminForm
	
	#class Media:
	#	css = {
	#		'all': ['eos_core_admin/css/icons.css']
	#	}
	
	def get_fieldsets(self, request, obj=None):
		return (
			(None, {'fields': ['id', 'election_name', 'election_url', 'workflow']}),
			('Schedule', {'fields':
				['voting_opens_at', 'voting_closes_at', 'voting_extended_until'] +
				(['voting_opened_at', 'open_voting'] if (obj is not None and obj.frozen_at and not obj.voting_has_opened) else ['voting_opened_at']) +
				(['voting_closed_at', 'close_voting'] if (obj is not None and obj.voting_has_opened and not obj.voting_has_closed) else ['voting_closed_at']) +
				(['result_released_at', 'release_result'] if (obj is not None and obj.result and not obj.result_released_at) else ['result_released_at'])
			}),
			('Questions', {'fields': ['questions']}),
			('Voters', {'fields': ['voter_eligibility']}),
			('Freeze Election', {'fields': ['frozen_at', 'freeze'] if (obj is None or not obj.frozen_at) else ['frozen_at']}),
		)
	
	def get_readonly_fields(self, request, obj=None):
		return (
			('id', 'election_url', 'frozen_at', 'voting_opened_at', 'voting_closed_at', 'result_released_at') +
			(('election_name', 'workflow', 'voting_opens_at', 'voting_closes_at', 'questions', 'voter_eligibility') if (obj is not None and obj.frozen_at) else ()) +
			(('voting_extended_until',) if (obj is None or not obj.voting_closes_at or obj.voting_closed_at) else ())
		)
	
	def election_url(self, obj):
		url = django.core.urlresolvers.reverse('election_view', args=[obj.id])
		return django.utils.safestring.mark_safe('<a href="' + url + '">' + url + '</a>')

django.contrib.admin.site.register(eos_core.models.Workflow, WorkflowAdmin)
django.contrib.admin.site.register(eos_core.models.Election, ElectionAdmin)
