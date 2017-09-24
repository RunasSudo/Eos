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

from eos.core.objects import EosObject

class BigInt(EosObject):
	def __init__(self, a, b=10):
		self.impl = int(a, b) if isinstance(a, str) else int(a)
	
	def __pow__(self, other, modulo=None):
		if not isinstance(other, BigInt):
			other = BigInt(other)
		if modulo is None:
			return BigInt(self.impl.__pow__(other.impl))
		if not isinstance(modulo, BigInt):
			modulo = BigInt(modulo)
		return BigInt(self.impl.__pow__(other.impl, modulo.impl))

for func in [
	'__add__', '__sub__', '__mul__', '__mod__', '__or__', '__lshift__', '__xor__',
	'__eq__', '__ne__', '__lt__', '__gt__', '__le__', '__ge__',
	'__str__'
]:
	def make_operator_func(func_):
		# Create a closure
		def operator_func(self, other):
			if not isinstance(other, BigInt):
				other = BigInt(other)
			return BigInt(getattr(self.impl, func_)(other.impl))
		return operator_func
	setattr(BigInt, func, make_operator_func(func))
