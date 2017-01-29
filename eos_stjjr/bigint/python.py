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

import random
system_random = random.SystemRandom()

class BigInt(eos_core.libobjects.EosObject):
	class EosMeta:
		eos_name = 'eos_stjjr.bigint.BigInt'
	
	def __init__(self, a, b=10):
		if isinstance(a, str):
			self.impl = int(a, b)
		elif isinstance(a, int):
			self.impl = int(a)
		else:
			raise Exception('Unsupported type passed to BigInt()')
	
	def __str__(self):
		return str(self.impl)
	
	def __int__(self):
		return self.impl
	
	def __eq__(self, other):
		if isinstance(other, BigInt):
			other = other.impl
		return self.impl == other
	def __lt__(self, other):
		if isinstance(other, BigInt):
			other = other.impl
		return self.impl < other
	def __gt__(self, other):
		if isinstance(other, BigInt):
			other = other.impl
		return self.impl > other
	def __le__(self, other):
		if isinstance(other, BigInt):
			other = other.impl
		return self.impl <= other
	def __ge__(self, other):
		if isinstance(other, BigInt):
			other = other.impl
		return self.impl >= other
	
	def __pow__(self, other, modulo=None):
		if isinstance(other, BigInt):
			other = other.impl
		if modulo is None:
			return self.impl.__pow__(other)
		if isinstance(modulo, BigInt):
			modulo = modulo.impl
		return BigInt(self.impl.__pow__(other, modulo))
	
	def serialise(self, hashed=False):
		return str(self.impl)
	
	@staticmethod
	def _deserialise(cls, value):
		return cls(value)

# Basic arithmetic operators
for key in ['__add__', '__sub__', '__mul__', '__floordiv__', '__mod__']:
	def wrapper(self, other, key=key):
		if isinstance(other, BigInt):
			other = other.impl
		return BigInt(getattr(self.impl, key)(other))
	setattr(BigInt, key, wrapper)

# Returns a random BigInt from lower_bound to upper_bound, both inclusive
def noncrypto_random(lower_bound, upper_bound):
	return BigInt(random.randint(int(lower_bound), int(upper_bound)))

def crypto_random(lower_bound, upper_bound):
	return BigInt(system_random.randint(int(lower_bound), int(upper_bound)))

ZERO = BigInt(0)
ONE = BigInt(1)
TWO = BigInt(2)
