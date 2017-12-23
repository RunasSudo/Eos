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

from eos.base.election import *
from eos.psr.election import *

model_view_map = {
	ApprovalQuestion: {
		'view': 'question/approval/view.html',
		'result_eos.base.election.RawResult': 'question/approval/result_raw.html',
		'selections_make': 'question/approval/selections_make.html',
		'selections_review': 'question/approval/selections_review.html'
	},
	Election: {
		'tabs': 'election/core/tabs.html'
	},
	PreferentialQuestion: {
		'view': 'question/preferential/view.html',
		'result_eos.base.election.RawResult': 'question/preferential/result_raw.html',
		'result_eos.base.election.STVResult': 'question/preferential/result_stv.html',
		'selections_make': 'question/preferential/selections_make.html',
		'selections_review': 'question/preferential/selections_review.html'
	},
	PSRElection: {
		'tabs': 'election/psr/tabs.html'
	}
}
