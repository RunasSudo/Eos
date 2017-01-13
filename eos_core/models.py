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
import eos_core.objects
import eos_basic.workflow

import django.core.exceptions
import django.db.models

import datetime
import uuid

class Question(eos_core.objects.EosObject):
	class EosMeta:
		abstract = True

class VoterEligibility(eos_core.objects.EosObject):
	class EosMeta:
		abstract = True

class EosDictObjectModelType(eos_core.objects.EosDictObjectType, django.db.models.base.ModelBase):
	def __new__(meta, name, bases, attrs):
		#import pdb; pdb.set_trace()
		meta, name, bases, attrs = eos_core.objects.EosDictObjectType._before_new(meta, name, bases, attrs)
		cls = django.db.models.base.ModelBase.__new__(meta, name, bases, attrs)
		cls = eos_core.objects.EosObjectType._after_new(cls, meta, name, bases, attrs)
		return cls
	
	def __call__(cls, *args, **kwargs):
		instance = django.db.models.base.ModelBase.__call__(cls, *args, **kwargs)
		instance = eos_core.objects.EosDictObjectType._after_call(instance, cls, *args, **kwargs)
		return instance

class EosDictObjectModel(django.db.models.Model, eos_core.objects.EosDictObject, metaclass=EosDictObjectModelType):
	class Meta:
		abstract = True

class Election(EosDictObjectModel):
	class EosMeta:
		eos_fields = [
			eos_core.objects.EosField(uuid.UUID, 'id', primary_key=True, editable=False),
			eos_core.objects.EosField(str, 'name', max_length=100),
			eos_core.objects.EosField('eos_core.Workflow', 'workflow', on_delete=django.db.models.PROTECT),
			
			eos_core.objects.EosField(list, 'questions'), # [eos_core.models.Question]
			eos_core.objects.EosField(eos_core.objects.EosObject, 'voter_eligibility'), # eos_core.models.VoterEligibility
			
			eos_core.objects.EosField(datetime.datetime, 'voting_starts_at', null=True),
			eos_core.objects.EosField(datetime.datetime, 'voting_ends_at', null=True),
			
			eos_core.objects.EosField(datetime.datetime, 'frozen_at', null=True),
			
			eos_core.objects.EosField(datetime.datetime, 'voting_extended_until', null=True),
			eos_core.objects.EosField(datetime.datetime, 'voting_started_at', null=True),
			eos_core.objects.EosField(datetime.datetime, 'voting_ended_at', null=True),
			eos_core.objects.EosField(datetime.datetime, 'result_released_at', null=True),
		]
	
	def __str__(self):
		return self.name

class Workflow(EosDictObjectModel):
	class EosMeta:
		eos_fields = [
			eos_core.objects.EosField(uuid.UUID, 'id', primary_key=True, editable=False),
			eos_core.objects.EosField(str, 'name', max_length=100),
			eos_core.objects.EosField(list, 'tasks'), # [eos_core.workflow.WorkflowTask]
		]
	
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
