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
from eos.core.tasks import *
from eos.base.election import *

import eos.base.util.blt

import pyRCV.stv
import pyRCV.utils.blt

import base64

class QuietSTVCounter(pyRCV.stv.STVCounter):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.randdata = base64.b64decode(self.args['randjson']['result']['random']['data'][0])
		
		self.output = []
	
	def log(self, string, *args):
		self.output.append(string.format(*args))

class TaskTallySTV(Task):
	election_id = UUIDField()
	q_num = IntField()
	random = BlobField()
	num_seats = IntField()
	
	def _run(self):
		election = Election.get_by_id(self.election_id)
		
		# Count the ballots
		blt = eos.base.util.blt.writeBLT(election, self.q_num, self.num_seats)
		ballots, candidates, seats = pyRCV.utils.blt.readBLT(blt)
		counter = QuietSTVCounter(ballots, candidates, seats=seats, ties=['backwards', 'random'], randjson=self.random, verbose=True, quota='gt-hb')
		elected, exhausted = counter.countVotes()
		
		election.results[self.q_num] = MultipleResult(results=[election.results[self.q_num]])
		result = STVResult(elected=[candidates.index(x) for x in elected], log='\n'.join(counter.output), random=self.random)
		
		election.results[self.q_num].results.append(result)
		election.save()
	
	@property
	def label(self):
		election = Election.get_by_id(self.election_id)
		return 'Tally STV question – ' + election.questions[self.q_num].prompt + ' – ' + election.name
