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

from eos.core.bigint import *
from eos.core.objects import *

class BitStream(EosObject):
	def __init__(self, value=None):
		if value:
			self.impl = value
			self.nbits = self.impl.nbits()
		else:
			self.impl = ZERO
			self.nbits = 0
		self.ptr = 0
		self.remaining = self.nbits
	
	def seek(self, ptr):
		self.ptr = ptr
		self.remaining = self.nbits - self.ptr
	
	def read(self, nbits=None):
		# 11000110110
		#    ^----
		if nbits is None:
			nbits = self.remaining
		if nbits > self.remaining:
			nbits = self.remaining
		
		val = (self.impl >> (self.remaining - nbits)) & ((ONE << nbits) - ONE)
		self.ptr += nbits
		self.remaining -= nbits
		return val
	
	def write(self, bits, nbits=None):
		# 11     0100110
		#   10010
		#   ^----
		if nbits is None:
			nbits = bits.nbits()
		
		self.impl = ((self.impl >> self.remaining) << (self.remaining + nbits)) | (bits << self.remaining) | (self.impl & ((ONE << self.remaining) - 1))
		self.ptr += nbits
		self.nbits += nbits
	
	# Make the size of this BitStream a multiple of the block_size
	def multiple_of(self, block_size):
		if self.nbits % block_size != 0:
			self.nbits += (block_size - (self.nbits % block_size))
		return self # For convenient chaining
	
	def map(self, func, block_size):
		if self.nbits % block_size != 0:
			raise Exception('The size of the BitStream must be a multiple of block_size')
		
		self.seek(0)
		result = []
		while self.remaining > 0:
			result.append(func(self.read(block_size)))
		return result
	
	@classmethod
	def unmap(cls, value, func, block_size):
		bs = cls()
		for x in value:
			bs.write(func(x), block_size)
		bs.seek(0)
		return bs
	
	def serialise(self):
		return self.impl
	
	@classmethod
	def deserialise(cls, value):
		return cls(value)
