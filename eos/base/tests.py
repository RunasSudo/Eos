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
		cls.db_connect_and_reset()
	
	def do_task_assert(self, election, task, next_task):
		self.assertEqual(election.workflow.get_task(task).status, WorkflowTask.Status.READY)
		if next_task is not None:
			self.assertEqual(election.workflow.get_task(next_task).status, WorkflowTask.Status.NOT_READY)
		election.workflow.get_task(task).enter()
		self.assertEqual(election.workflow.get_task(task).status, WorkflowTask.Status.EXITED)
		if next_task is not None:
			self.assertEqual(election.workflow.get_task(next_task).status, WorkflowTask.Status.READY)
	
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
			voter = Voter(name=['Alice', 'Bob', 'Charlie'][i])
			election.voters.append(voter)
			# Check _instance
			self.assertEqual(voter._instance, (election.voters, i))
		
		question = ApprovalQuestion(prompt='President', choices=[Choice(name='John Smith'), Choice(name='Joe Bloggs'), Choice(name='John Q. Public')])
		election.questions.append(question)
		
		question = ApprovalQuestion(prompt='Chairman', choices=[Choice(name='John Doe'), Choice(name='Andrew Citizen')])
		election.questions.append(question)
		
		election.save()
		
		# Check that it saved
		self.assertEqual(Election.get_all()[0], election)
		
		self.assertEqualJSON(EosObject.deserialise_and_unwrap(EosObject.serialise_and_wrap(election)).serialise(), election.serialise())
		
		# Freeze election
		self.do_task_assert(election, 'eos.base.workflow.TaskConfigureElection', 'eos.base.workflow.TaskOpenVoting')
		election.save()
		
		# Try to freeze it again
		try:
			election.workflow.get_task('eos.base.workflow.TaskConfigureElection').exit()
			self.fail()
		except Exception:
			pass
		
		election_hash = SHA256().update_obj(election).hash_as_b64()
		
		# Open voting
		self.do_task_assert(election, 'eos.base.workflow.TaskOpenVoting', 'eos.base.workflow.TaskCloseVoting')
		election.save()
		
		# Cast ballots
		VOTES = [[[0], [0]], [[0, 1], [1]], [[2], [0]]]
		
		for i in range(3):
			ballot = Ballot(election_id=election._id, election_hash=election_hash)
			for j in range(2):
				answer = ApprovalAnswer(choices=VOTES[i][j])
				encrypted_answer = NullEncryptedAnswer(answer=answer)
				ballot.encrypted_answers.append(encrypted_answer)
			vote = Vote(ballot=ballot, cast_at=DateTimeField.now())
			election.voters[i].votes.append(vote)
		
		election.save()
		
		# Close voting
		self.do_task_assert(election, 'eos.base.workflow.TaskCloseVoting', 'eos.base.workflow.TaskDecryptVotes')
		election.save()
		
		# "Decrypt" votes
		self.do_task_assert(election, 'eos.base.workflow.TaskDecryptVotes', 'eos.base.workflow.TaskReleaseResults')
		election.save()
		
		# Check result
		RESULTS = [[[0], [0, 1], [2]], [[0], [1], [0]]]
		for i in range(len(RESULTS)):
			votes1 = RESULTS[i]
			votes2 = [x.choices for x in election.results[i].answers]
			self.assertEqual(sorted(votes1), sorted(votes2))
		
		# Release result
		self.do_task_assert(election, 'eos.base.workflow.TaskReleaseResults', None)
		election.save()
