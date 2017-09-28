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

try:
	__pragma__ = __pragma__
	is_python = False
except:
	is_python = True
	def __pragma__(*args):
		pass

from eos.core.bigint import *

# Libraries
# =========

if is_python:
	__pragma__('skip')
	import base64
	import hashlib
	__pragma__('noskip')
else:
	# Load jssha-sha256.js
	lib = __pragma__('js', '''
	(function() {{
		{}
		var exports = {{}};
		exports.jsSHA = window.jsSHA;
		return exports;
	}})()''', __include__('eos/core/hashing/jssha-sha256.js'))

# Implementation
# ==============

class SHA256:
	def __init__(self):
		if is_python:
			self.impl = hashlib.sha256()
		else:
			# TNYI: This is completely borked
			self.impl = __pragma__('js', '{}', 'new lib.jsSHA("SHA-256", "TEXT")')
	
	def update_text(self, *values):
		for value in values:
			if is_python:
				self.impl.update(value.encode('utf-8'))
			else:
				self.impl.js_update(value)
		return self
	
	def update_bigint(self, *values):
		for value in values:
			self.update_text(str(value))
		return self
	
	def hash_as_b64(self):
		if is_python:
			return base64.b64encode(self.impl.digest()).decode('utf-8')
		else:
			return self.impl.getHash('B64')
	
	def hash_as_hex(self):
		if is_python:
			return self.impl.hexdigest()
		else:
			return self.impl.getHash('HEX')
	
	def hash_as_bigint(self):
		return BigInt(self.hash_as_hex(), 16)
