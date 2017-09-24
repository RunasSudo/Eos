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
			('__or__', 'or'),
			('__lshift__', 'shiftLeft'),
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
	
	def __pow__(self, other, modulo=None):
		if not isinstance(other, BigInt):
			other = BigInt(other)
		if modulo is None:
			return BigInt(self.impl.pow(other.impl))
		if not isinstance(modulo, BigInt):
			modulo = BigInt(modulo)
		return BigInt(self.impl.modPow(other.impl, modulo.impl))
