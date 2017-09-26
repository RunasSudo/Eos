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

import random

# Load jsbn{,2}.js
lib = __pragma__('js', '''
(function() {{
	var exports = {{}};
	{}
	{}
	exports.BigInteger = BigInteger;
	exports.nbi = nbi;
	exports.nbv = nbv;
	exports.Classic = Classic;
	exports.Montgomery = Montgomery;
	exports.NullExp = NullExp;
	exports.Barrett = Barrett;
	return exports;
}})()''', __include__('eos/core/bigint/jsbn.js'), __include__('eos/core/bigint/jsbn2.js'))

class BigInt(EosObject):
	def __init__(self, a, b=10):
		super().__init__()
		
		if isinstance(a, str):
			self.impl = lib.nbi()
			self.impl.fromString(a, b)
		elif isinstance(a, int):
			self.impl = lib.nbv(a)
		elif type(a) is not None and hasattr(a, '__proto__') and a.__proto__ == lib.BigInteger.prototype:
			self.impl = a
		else:
			console.error('Unsupported type passed to BigInt()')
			raise Exception()
		
		# Basic arithmetic operators
		# TNYI: Transcrypt drops the self parameter when calling operator_func for some strange reason, so we must define these at the instance level
		for key, func in [
			('__add__', 'add'),
			('__sub__', 'subtract'),
			('__mul__', 'multiply'),
			('__mod__', 'mod'),
			('__and__', 'and'),
			('__or__', 'or'),
			('__lshift__', 'shiftLeft'),
			('__rshift__', 'shiftRight'),
			('__xor__', 'xor')
		]:
			def make_operator_func(func_):
				# Create a closure
				def operator_func(other):
					if not isinstance(other, BigInt):
						other = BigInt(other)
					# TNYI: We must explicitly bind() this function
					return BigInt((getattr(self.impl, func_).bind(self.impl))(other.impl))
				return operator_func
			setattr(self, key, make_operator_func(func))
		
		for key, func in [
			('__eq__', lambda x: x == 0),
			('__ne__', lambda x: x != 0),
			('__lt__', lambda x: x < 0),
			('__gt__', lambda x: x > 0),
			('__le__', lambda x: x <= 0),
			('__ge__', lambda x: x >= 0)
		]:
			def make_operator_func(func_):
				def operator_func(other):
					if not isinstance(other, BigInt):
						other = BigInt(other)
					return func_(self.impl.compareTo(other.impl))
				return operator_func
			setattr(self, key, make_operator_func(func))
	
	def __str__(self):
		return str(self.impl)
	
	def __int__(self):
		# WARNING: This will yield unexpected results for large numbers
		return int(str(self.impl))
	
	def __pow__(self, other, modulo=None):
		if not isinstance(other, BigInt):
			other = BigInt(other)
		if modulo is None:
			return BigInt(self.impl.pow(other.impl))
		if not isinstance(modulo, BigInt):
			modulo = BigInt(modulo)
		return BigInt(self.impl.modPow(other.impl, modulo.impl))
	
	def nbits(self):
		return self.impl.bitLength()
	
	def serialise(self):
		return str(self)
	
	@classmethod
	def deserialise(cls, value):
		return cls(value)
	
	# Returns a random BigInt from lower_bound to upper_bound, both inclusive
	@classmethod
	def noncrypto_random(cls, lower_bound, upper_bound):
		if not isinstance(lower_bound, cls):
			lower_bound = cls(lower_bound)
		if not isinstance(upper_bound, cls):
			upper_bound = cls(upper_bound)
		
		bound_range = upper_bound - lower_bound + 1
		bound_range_bits = bound_range.impl.bitLength()
		
		# Generate a sufficiently large number; work 32 bits at a time
		current_range = 0 # bits
		max_int = 2 ** 32 - 1
		big_number = cls(0)
		while current_range < bound_range_bits:
			random_number = cls(random.randint(0, max_int))
			big_number = (big_number << 32) | random_number
			current_range = current_range + 32
		
		# Since this is the non-crypto version, just do it modulo
		return lower_bound + (big_number % bound_range)
	
	@classmethod
	def crypto_random(cls, lower_bound, upper_bound):
		# TODO
		return cls.noncrypto_random(lower_bound, upper_bound)

# TNYI: No native pow() support
def pow(a, b, c=None):
	if not isinstance(a, BigInt):
		a = BigInt(a)
	return a.__pow__(b, c)
