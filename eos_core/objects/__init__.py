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

eos_objects = {}

if eos_core.is_python:
	__pragma__ = lambda x: None
	__pragma__('skip')
	from eos_core.objects.python import *
	__pragma__('noskip')
else:
	from eos_core.objects.js import *

# Must declare eos_fields field
class EosDictObject(EosObject, metaclass=EosDictObjectType):
	class EosMeta:
		abstract = True
	
	def __init__(self, *args, **kwargs):
		if eos_core.is_python:
			__pragma__('skip')
			import django.db.models
			if isinstance(self, django.db.models.Model):
				# Allow Django to manage setup
				super().__init__(*args, **kwargs)
				return
			__pragma__('noskip')
		
		# Emulate Django and set the fields
		#super().__init__()
		
		# We must handle both regular Python convention (kwargs) and Javascript-compatible syntax (args object)
		if len(args) == 1 and len(kwargs) == 0 and typeof(args[0]) == "object":
			__pragma__('jsiter')
			for arg in args[0]:
				kwargs[arg] = args[0][arg]
			__pragma__('nojsiter')
			args.pop()
		
		fields = [field.name for field in self._eosmeta.eos_fields]
		__pragma__('jsiter')
		for arg in kwargs:
			if arg in fields and not hasattr(self, arg):
				setattr(self, arg, kwargs[arg])
		__pragma__('nojsiter')
	
	def serialise(self, hashed=False):
		result = {}
		for field in self._eosmeta.eos_fields:
			if not hashed or field.hashed:
				result[field.name] = EosObject.serialise_and_wrap(getattr(self, field.name), field, hashed)
		return result
	
	@classmethod
	def deserialise(cls, value):
		result = {}
		for field in cls._eosmeta.eos_fields:
			result[field.name] = EosObject.deserialise_and_unwrap(value[field.name], field)
		return cls(**result)

def to_json(value):
	return json.dumps(value, sort_keys=True)

def from_json(value):
	return json.loads(value)
