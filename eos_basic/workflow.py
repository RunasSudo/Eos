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

import eos_basic.objects
import eos_core.libobjects
import eos_core.workflow

if eos_core.is_python:
	__pragma__ = lambda x: None
	__pragma__('skip')
	import django.core.urlresolvers
	__pragma__('noskip')

class EosDictObjectWorkflowTaskType(eos_core.libobjects.EosDictObjectType, eos_core.workflow.WorkflowTaskType):
	def __new__(meta, name, bases, attrs):
		meta, name, bases, attrs = eos_core.libobjects.EosDictObjectType._before_new(meta, name, bases, attrs)
		cls = eos_core.workflow.WorkflowTaskType.__new__(meta, name, bases, attrs)
		cls = eos_core.libobjects.EosObjectType._after_new(cls, meta, name, bases, attrs)
		return cls

class EosDictObjectWorkflowTask(eos_core.workflow.WorkflowTask, eos_core.libobjects.EosDictObject, metaclass=EosDictObjectWorkflowTaskType):
	class EosMeta:
		abstract = True
	
	def __init__(self, *args, **kwargs):
		eos_core.workflow.WorkflowTask.__init__(self)
		eos_core.libobjects.EosDictObject.__init__(self, *args, **kwargs)

class TaskReceiveVotes(EosDictObjectWorkflowTask):
	workflow_provides = ['eos_core.workflow.TaskReceiveVotes']
	workflow_depends = ['eos_core.workflow.TaskOpenVoting']
	
	class EosMeta:
		eos_name = 'eos_basic.workflow.TaskReceiveVotes'
		eos_fields = [
			eos_core.libobjects.EosField(list, 'booth_tasks') # [eos_basic.workflow.BoothTask]
		]
	
	def task_name(self, workflow, election):
		return 'Cast votes'
	
	def task_url(self, workflow, election):
		return django.core.urlresolvers.reverse('election_voting_booth', args=[election.id])
	
	def is_complete(self, workflow, election):
		# We are never finished receiving votes
		return False
	
	def are_restrictions_met(self, workflow, election):
		if not EosDictObjectWorkflowTask.are_restrictions_met(self, workflow, election):
			return False
		return election.voting_has_opened and not election.voting_has_closed

class TaskComputeResult(eos_core.workflow.TaskComputeResult):
	workflow_provides = 'eos_core.workflow.TaskComputeResult'
	workflow_depends = ['eos_core.workflow.TaskCloseVoting']
	
	class EosMeta:
		eos_name = 'eos_basic.workflow.TaskComputeResult'
	
	def compute_result(self, workflow, election):
		#import pdb; pdb.set_trace()
		
		# Collect the plaintexts
		question_plaintexts = [[] for _ in range(len(election.questions))]
		
		for cast_vote in election.get_valid_votes():
			plaintext_vote = cast_vote.encrypted_vote.to_plaintext_vote()
			for question_num, question_choices in enumerate(plaintext_vote.choices):
				question_plaintexts[question_num].append(question_choices)
		
		# Compute the results
		results = []
		for question_num, question in enumerate(election.questions):
			question_result = eos_basic.objects.ApprovalQuestionResult(tally=[0 for _ in range(len(question.choices))])
			for ballot in question_plaintexts[question_num]:
				for choice in ballot:
					question_result.tally[choice] += 1
			results.append(question_result)
		
		election.result = results
		election.save()
	
	def is_complete(self, workflow, election):
		return election.result is not None


booth_tasks = {}

class BoothTaskType(eos_core.libobjects.EosObjectType):
	def __new__(meta, name, bases, attrs):
		#cls = super().__new__(meta, name, bases, attrs)
		cls = eos_core.libobjects.EosObjectType.__new__(meta, name, bases, attrs)
		
		if not getattr(cls._eosmeta, 'abstract', False):
			booth_tasks[eos_core.libobjects.get_full_name(cls)] = cls
		
		return cls

class BoothTask(eos_core.libobjects.EosObject, metaclass=BoothTaskType):
	workflow_provides = []
	workflow_depends = []
	#workflow_conflicts = []
	#workflow_after = []
	workflow_before = []
	
	class EosMeta:
		abstract = True
	
	@staticmethod
	def get_all():
		if eos_core.is_python:
			__pragma__ = lambda x: None
			__pragma__('skip')
			import eos.settings
			import importlib
			for app in eos.settings.INSTALLED_APPS:
				try:
					importlib.import_module(app + '.workflow')
				except ImportError:
					pass
			__pragma__('noskip')
		return booth_tasks

class NullBoothTask(BoothTask):
	class EosMeta:
		abstract = True
	
	def serialise(self, hashed=False):
		return None
	
	@staticmethod
	def _deserialise(cls, value):
		return cls()

class NullTemplateBoothTask(NullBoothTask):
	class EosMeta:
		abstract = True
	
	def get_main_template(self):
		return self.get_templates()[0]
	
	def activate(self, fromFront):
		# Hand over to JavaScript
		showTemplate(self.get_main_template())

class BoothTaskWelcome(NullTemplateBoothTask):
	class EosMeta:
		eos_name = 'eos_basic.workflow.BoothTaskWelcome'
	
	def get_templates(self):
		return ['eos_basic/templates/landing.html', 'eos_basic/templates/base.html']

class BoothTaskMakeSelections(NullBoothTask):
	class EosMeta:
		eos_name = 'eos_basic.workflow.BoothTaskMakeSelections'
	
	def get_templates(self):
		return ['eos_basic/templates/selections.html', 'eos_basic/templates/question.html']
	
	def activate(self, fromFront):
		# Hand over to JavaScript
		if fromFront:
			showTemplate(self.get_templates()[0], '#booth-content', { 'questionNum': 0 })
		else:
			showTemplate(self.get_templates()[0], '#booth-content', { 'questionNum': election.questions.length - 1 })

class BoothTaskReviewSelections(NullTemplateBoothTask):
	class EosMeta:
		eos_name = 'eos_basic.workflow.BoothTaskReviewSelections'
	
	def get_templates(self):
		return ['eos_basic/templates/review.html']

class BoothTaskEncryptBallot(NullTemplateBoothTask):
	class EosMeta:
		eos_name = 'eos_basic.workflow.BoothTaskEncryptBallot'
	
	def get_templates(self):
		return ['eos_basic/templates/encrypt.html']
	
	def activate(self, fromFront):
		if fromFront:
			NullTemplateBoothTask.activate(self, fromFront)
		else:
			# If going back, skip straight to the review page
			prevTemplate()

class BoothTaskAuditBallot(NullTemplateBoothTask):
	class EosMeta:
		eos_name = 'eos_basic.workflow.BoothTaskAuditBallot'
	
	def get_templates(self):
		return ['eos_basic/templates/audit.html']

class BoothTaskCastVote(NullTemplateBoothTask):
	class EosMeta:
		eos_name = 'eos_basic.workflow.BoothTaskCastVote'
	
	def get_templates(self):
		return ['eos_basic/templates/cast.html', 'eos_basic/templates/complete.html']
