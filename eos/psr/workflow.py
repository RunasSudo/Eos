#   Eos - Verifiable elections
#   Copyright © 2017  RunasSudo (Yingtong Li)
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

from eos.core.objects import *
from eos.base.workflow import *
import eos.base.workflow

# Concrete tasks
# ==============

class TaskMixVotes(WorkflowTask):
	depends_on = ['eos.base.workflow.TaskCloseVoting']
	
	def on_enter(self):
		election = self.recurse_parents('eos.base.election.Election')
		
		should_exit = True
		
		for i in range(len(election.questions)):
			for j in range(len(election.mixing_trustees)):
				success = election.mixing_trustees[j].mix_votes(i)
				if not success:
					should_exit = False
					break # out of inner loop - further mixing required by hand for this question
		
		if should_exit:
			self.exit()

class TaskProveMixes(WorkflowTask):
	depends_on = ['eos.psr.workflow.TaskMixVotes']
	
	def on_enter(self):
		election = self.recurse_parents('eos.base.election.Election')
		
		should_exit = True
		
		for i in range(len(election.questions)):
			for j in range(len(election.mixing_trustees)):
				success = election.mixing_trustees[j].prove_mixes(i)
				if not success:
					should_exit = False
					break # out of inner loop - further mixing required by hand for this question
		
		if should_exit:
			self.exit()

class TaskDecryptVotes(eos.base.workflow.TaskDecryptVotes):
	depends_on = ['eos.psr.workflow.TaskProveMixes']
	
	def on_enter(self):
		election = self.recurse_parents('eos.base.election.Election')
		
		for _ in range(len(election.questions)):
			election.results.append(EosObject.objects['eos.base.election.RawResult']())
		
		for i in range(len(election.mixing_trustees[-1].mixed_questions)):
			for encrypted_answer in election.mixing_trustees[-1].mixed_questions[i]:
				answer = encrypted_answer.decrypt()
				election.results[i].answers.append(answer)
		
		self.exit()

# Concrete workflows
# ==================

class PSRWorkflow(Workflow):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		self.tasks.append(TaskConfigureElection())
		self.tasks.append(TaskOpenVoting())
		self.tasks.append(TaskCloseVoting())
		self.tasks.append(TaskMixVotes())
		self.tasks.append(TaskProveMixes())
		self.tasks.append(TaskDecryptVotes()) # The PSR one, not the base one
		self.tasks.append(TaskReleaseResults())
