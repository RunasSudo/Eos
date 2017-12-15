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

import math

import random
system_random = random.SystemRandom()

class BigInt(EosObject):
	def __init__(self, a, b=10):
		super().__init__()
		
		self.impl = int(a, b) if isinstance(a, str) else int(a)
	
	def __repr__(self):
		return '<BigInt {}>'.format(str(self))
	
	def __pow__(self, other, modulo=None):
		if not isinstance(other, BigInt):
			other = BigInt(other)
		if modulo is None:
			return BigInt(self.impl.__pow__(other.impl))
		if not isinstance(modulo, BigInt):
			modulo = BigInt(modulo)
		return BigInt(self.impl.__pow__(other.impl, modulo.impl))
	
	def __truediv__(self, other):
		# Python will try to compute this as a float
		return self.__floordiv__(other)
	
	def nbits(self):
		return math.ceil(math.log2(self.impl)) if self.impl > 0 else 0
	
	def serialise(self, options=SerialiseOptions.DEFAULT):
		return str(self)
	
	@classmethod
	def deserialise(cls, value):
		if value is None:
			return None
		return cls(value)
	
	# Returns a random BigInt from lower_bound to upper_bound, both inclusive
	@classmethod
	def noncrypto_random(cls, lower_bound, upper_bound):
		return cls(random.randint(int(lower_bound), int(upper_bound)))
	
	@classmethod
	def crypto_random(cls, lower_bound, upper_bound):
		return cls(system_random.randint(int(lower_bound), int(upper_bound)))

for func in ['__add__', '__sub__', '__mul__', '__floordiv__', '__mod__', '__and__', '__or__', '__lshift__', '__rshift__', '__xor__']:
	def make_operator_func(func_):
		# Create a closure
		def operator_func(self, other):
			if not isinstance(other, BigInt):
				other = BigInt(other)
			return BigInt(getattr(self.impl, func_)(other.impl))
		return operator_func
	setattr(BigInt, func, make_operator_func(func))

for func in ['__eq__', '__ne__', '__lt__', '__gt__', '__le__', '__ge__']:
	def make_operator_func(func_):
		# Create a closure
		def operator_func(self, other):
			if not isinstance(other, BigInt):
				other = BigInt(other)
			return getattr(self.impl, func_)(other.impl)
		return operator_func
	setattr(BigInt, func, make_operator_func(func))

for func in ['__neg__']:
	def make_operator_func(func_):
		# Create a closure
		def operator_func(self):
			return BigInt(getattr(self.impl, func_)())
		return operator_func
	setattr(BigInt, func, make_operator_func(func))

for func in ['__str__', '__int__']:
	def make_operator_func(func_):
		# Create a closure
		def operator_func(self):
			return getattr(self.impl, func_)()
		return operator_func
	setattr(BigInt, func, make_operator_func(func))
