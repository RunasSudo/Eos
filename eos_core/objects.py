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

import eos_core.libobjects

class Question(eos_core.libobjects.EosObject):
	class EosMeta:
		abstract = True

class VoterEligibility(eos_core.libobjects.EosObject):
	class EosMeta:
		abstract = True

class Voter(eos_core.libobjects.EosObject):
	class EosMeta:
		abstract = True

# Represents a vote in hashable form, which is likely but not necessarily encrypted
class EncryptedVote(eos_core.libobjects.EosObject):
	class EosMeta:
		abstract = True

class PlaintextVote(EncryptedVote, eos_core.libobjects.EosDictObject):
	class EosMeta:
		eos_name = 'eos_core.models.PlaintextVote'
