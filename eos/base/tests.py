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

from unittest import TestCase

from eos.base.election import *
from eos.base.workflow import *
from eos.core.objects import *

class ElectionTestCase(TestCase):
	@classmethod
	def setUpClass(cls):
		client.drop_database('test')
	
	def test_run_election(self):
		# Set up election
		election = Election()
		election.workflow = WorkflowBase(election)
		
		self.assertEqual(election.workflow.get_task('eos.base.workflow.TaskConfigureElection').status, WorkflowTask.Status.READY)
		
		election.name = 'Test Election'
		
		for i in range(3):
			election.voters.append(Voter())
		
		question = ApprovalQuestion(prompt='President', choices=['John Smith', 'Joe Bloggs', 'John Q. Public'])
		election.questions.append(question)
		
		question = ApprovalQuestion(prompt='Chairman', choices=['John Doe', 'Andrew Citizen'])
		election.questions.append(question)
		
		election.save()
		
		# Check that it saved
		self.assertEqual(db[Election._name].find_one(), election.serialise())
		
		# Freeze election
		self.assertEqual(election.workflow.get_task('eos.base.workflow.TaskConfigureElection').status, WorkflowTask.Status.READY)
		self.assertEqual(election.workflow.get_task('eos.base.workflow.TaskOpenVoting').status, WorkflowTask.Status.NOT_READY)
		election.workflow.get_task('eos.base.workflow.TaskConfigureElection').exit()
		self.assertEqual(election.workflow.get_task('eos.base.workflow.TaskConfigureElection').status, WorkflowTask.Status.EXITED)
		self.assertEqual(election.workflow.get_task('eos.base.workflow.TaskOpenVoting').status, WorkflowTask.Status.READY)
		
		election.save()
		
		# Cast ballots
		VOTES = [[[0], [0]], [[0, 1], [1]], [[2], [0]]]
		
		for i in range(3):
			ballot = Ballot()
			for j in range(2):
				answer = ApprovalAnswer(choices=VOTES[i][j])
				encrypted_answer = NullEncryptedAnswer(answer=answer)
				ballot.encrypted_answers.append(encrypted_answer)
			election.voters[i].ballots.append(ballot)
		
		election.save()
