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

import eos_core

if eos_core.is_python:
	__pragma__ = lambda x: None
	__pragma__('skip')
	
	import base64
	import hashlib
	
	# Pass strings
	def hash_as_b64(*values):
		h = hashlib.sha256()
		for value in values:
			h.update(value.encode('utf-8'))
		return base64.b64encode(h.digest()).decode('utf-8')
	
	def hash_as_hex(*values):
		h = hashlib.sha256()
		for value in values:
			h.update(value.encode('utf-8'))
		return h.hexdigest()
	
	__pragma__('noskip')
else:
	def hash_as_b64(*values):
		sha = __new__(jsSHA('SHA-256', 'TEXT'))
		for value in values:
			getattr(sha, 'update')(value)
		return sha.getHash('B64')
	
	def hash_as_hex(*values):
		sha = __new__(jsSHA('SHA-256', 'TEXT'))
		for value in values:
			getattr(sha, 'update')(value)
		return sha.getHash('HEX')
