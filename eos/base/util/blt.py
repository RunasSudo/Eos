#   Eos - Verifiable elections
#   pyRCV - Preferential voting counting
#   Copyright © 2016–2017  RunasSudo (Yingtong Li)
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

def writeBLT(election, q_num, seats, withdrawn=[]):
	question = election.questions[q_num]
	flat_choices = question.flatten_choices()
	
	electionLines = []
	
	electionLines.append('{} {}'.format(len(flat_choices), seats))
	
	if len(withdrawn) > 0:
		electionLines.append(' '.join(['-{}'.format(flat_choices.index(candidate) + 1) for candidate in withdrawn]))
	
	result = election.results[q_num].count()
	
	for answer, count in result:
		if answer.choices:
			electionLines.append('{} {} 0'.format(count, ' '.join(str(x + 1) for x in answer.choices)))
		else:
			electionLines.append('{} 0'.format(count))
	
	electionLines.append('0')
	
	for candidate in flat_choices:
		if candidate.party:
			electionLines.append("'{} – {}'".format(candidate.name, candidate.party))
		else:
			electionLines.append("'{}'".format(candidate.name))
	
	electionLines.append("'{} – {}'".format(election.name, question.prompt))
	
	return electionLines
