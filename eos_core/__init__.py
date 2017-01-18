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

try:
	__pragma__
	is_python = False
	
	def tclassmethod(func):
		# TNYI: Transcrypt seems to pass the class as "this" rather than the first parameter
		@classmethod
		def wrapper(*args, **kwargs):
			return func(this, *args, **kwargs)
		return wrapper
except:
	is_python = True
	
	def tclassmethod(func):
		@classmethod
		def wrapper(*args, **kwargs):
			return func(*args, **kwargs)
		return wrapper
