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

from eos.core.tests import *

from eos.base.election import *
from eos.base.workflow import *
from eos.core.objects import *

class ElectionTestCase(EosTestCase):
	@classmethod
	def setUpClass(cls):
		if is_python:
			client.drop_database('test')
	
	def exit_task_assert(self, election, task, next_task):
		self.assertEqual(election.workflow.get_task(task).status, WorkflowTask.Status.READY)
		self.assertEqual(election.workflow.get_task(next_task).status, WorkflowTask.Status.NOT_READY)
		election.workflow.get_task(task).exit()
		self.assertEqual(election.workflow.get_task(task).status, WorkflowTask.Status.EXITED)
		self.assertEqual(election.workflow.get_task(next_task).status, WorkflowTask.Status.READY)
	
	def save_if_python(self, obj):
		if is_python:
			obj.save()
	
	@py_only
	def test_run_election(self):
		# Set up election
		election = Election()
		election.workflow = WorkflowBase()
		
		# Check _instance
		self.assertEqual(election.workflow._instance, (election, 'workflow'))
		
		# Check workflow behaviour
		self.assertEqual(election.workflow.get_task('eos.base.workflow.TaskConfigureElection').status, WorkflowTask.Status.READY)
		self.assertEqual(election.workflow.get_task('does.not.exist'), None)
		
		# Set election details
		election.name = 'Test Election'
		
		for i in range(3):
			voter = Voter()
			election.voters.append(voter)
			# Check _instance
			self.assertEqual(voter._instance, (election.voters, i))
		
		question = ApprovalQuestion(prompt='President', choices=['John Smith', 'Joe Bloggs', 'John Q. Public'])
		election.questions.append(question)
		
		question = ApprovalQuestion(prompt='Chairman', choices=['John Doe', 'Andrew Citizen'])
		election.questions.append(question)
		
		self.save_if_python(election)
		
		# Check that it saved
		if is_python:
			self.assertEqual(db[Election._name].find_one()['value'], election.serialise())
			self.assertEqual(EosObject.deserialise_and_unwrap(db[Election._name].find_one()).serialise(), election.serialise())
		
		self.assertEqualJSON(EosObject.deserialise_and_unwrap(EosObject.serialise_and_wrap(election)).serialise(), election.serialise())
		
		# Freeze election
		self.exit_task_assert(election, 'eos.base.workflow.TaskConfigureElection', 'eos.base.workflow.TaskOpenVoting')
		self.save_if_python(election)
		
		# Try to freeze it again
		try:
			election.workflow.get_task('eos.base.workflow.TaskConfigureElection').exit()
			self.fail()
		except Exception:
			pass
		
		# Cast ballots
		VOTES = [[[0], [0]], [[0, 1], [1]], [[2], [0]]]
		
		for i in range(3):
			ballot = Ballot()
			for j in range(2):
				answer = ApprovalAnswer(choices=VOTES[i][j])
				encrypted_answer = NullEncryptedAnswer(answer=answer)
				ballot.encrypted_answers.append(encrypted_answer)
			election.voters[i].ballots.append(ballot)
		
		self.save_if_python(election)
		
		# Close voting
		self.exit_task_assert(election, 'eos.base.workflow.TaskOpenVoting', 'eos.base.workflow.TaskCloseVoting')
		self.save_if_python(election)
		
		# Compute result
		election.results = [None, None]
		for i in range(2):
			result = election.questions[i].compute_result()
			election.results[i] = result
		
		self.save_if_python(election)
		
		self.assertEqual(election.results[0].choices, [2, 1, 1])
		self.assertEqual(election.results[1].choices, [2, 1])
