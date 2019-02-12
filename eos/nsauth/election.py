#   Eos - Verifiable elections
#   Copyright © 2017-2019  RunasSudo (Yingtong Li)
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
from eos.core.objects import *

class NationStatesUser(User):
	username = StringField()
	
	@property
	def name(self):
		return self.username
	
	def matched_by(self, other):
		if not isinstance(other, NationStatesUser):
			return False
		return other.username.lower().strip().replace(' ', '_') == self.username.lower().strip().replace(' ', '_')
