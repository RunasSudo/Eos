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

datetime = str
uuid = str

eos_objects = {}

# TNYI
def issubclass(cls1, cls2):
	if cls1 == cls2:
		return True
	if hasattr(cls1, '__bases__'):
		for base in cls1.__bases__:
			if issubclass(base, cls2):
				return True
	return False

def get_full_name(obj):
	if typeof(obj) != 'function':
		obj = type(obj)
	
	if obj is list:
		return 'builtins.' + obj.__name__
	
	if hasattr(obj, '_eosmeta'):
		if hasattr(obj._eosmeta, 'eos_name'):
			return obj._eosmeta.eos_name
	
	raise ('Unknown full name for object ' + obj.__name__)

class EosObjectType(type):
	def __new__(meta, name, bases, attrs):
		cls = type.__new__(meta, name, bases, attrs)
		cls = EosObjectType._after_new(cls, meta, name, bases, attrs)
		return cls
	
	def _after_new(cls, meta, name, bases, attrs):
		base_meta = getattr(cls, '_eosmeta', None)
		attr_meta = attrs['EosMeta'] if 'EosMeta' in attrs else {}
		if base_meta and getattr(base_meta, 'abstract', False) and not hasattr(attr_meta, 'abstract'):
			# Don't inherit the abstract field by default
			cls.EosMeta.abstract = False
		cls._eosmeta = cls.EosMeta
		
		if not getattr(cls._eosmeta, 'abstract', False):
			eos_objects[get_full_name(cls)] = cls
		
		return cls

# An object that can be serialised
class EosObject(metaclass=EosObjectType):
	class EosMeta:
		abstract = True
	
	def __str__(self):
		return to_json(EosObject.serialise_and_wrap(self, None))
	
	def __eq__(self, other):
		return (get_full_name(self) == get_full_name(other)) and (self.serialise() == other.serialise())
	
	@staticmethod
	def get_all():
		return eos_objects
	
	@staticmethod
	def serialise_and_wrap(value, value_type, hashed=False):
		if value is None:
			return value
		if value_type is not None and value_type.py_type is not EosObject:
			# The value type is guaranteed, so store directly
			if isinstance(value_type.py_type, str):
				# ForeignKey
				return value.serialise(hashed)
			if issubclass(value_type.py_type, EosObject):
				return value.serialise(hashed)
			elif issubclass(value_type.py_type, list):
				return EosObject.serialise_list(value, value_type.element_type, hashed)
			# TODO
			#elif issubclass(value_type.py_type, uuid.UUID):
			#	return str(value)
			#elif issubclass(value_type.py_type, datetime.datetime):
			#	return value.astimezone(django.utils.timezone.utc).isoformat()
			else:
				return value
		else:
			# The value type is unknown, so store wrapped
			if isinstance(value, EosObject):
				return { 'type': get_full_name(value), 'value': value.serialise(hashed) }
			elif isinstance(value, list):
				return { 'type': get_full_name(value), 'value': EosObject.serialise_list(value, None, hashed) }
			# TODO
			#elif isinstance(value, uuid.UUID):
			#	return { 'type': get_full_name(value), 'value': str(value) }
			else:
				return { 'type': get_full_name(value), 'value': value }
	
	@staticmethod
	def serialise_list(value, element_type, hashed=False):
		if value is None:
			return value
		return [EosObject.serialise_and_wrap(element, element_type, hashed) for element in value]
	
	@staticmethod
	def deserialise_and_unwrap(value, value_type):
		if value_type is not None and value_type.py_type is not EosObject:
			# The value type is guaranteed, so should be stored directly
			if issubclass(value_type.py_type, EosObject):
				return value_type.py_type.deserialise(value)
			elif issubclass(value_type.py_type, list):
				return EosObject.deserialise_list(value, value_type.element_type)
			else:
				return value
		else:
			# The value type is unknown, so should be stored wrapped
			if value['type'] in eos_objects:
				return eos_objects[value['type']].deserialise(value['value'])
			elif value['type'] == get_full_name(list):
				return EosObject.deserialise_list(value['value'], None)
			else:
				return value['value']
	
	@staticmethod
	def deserialise_list(value, element_type):
		if value is None:
			return value
		return [EosObject.deserialise_and_unwrap(element, element_type) for element in value]
	
	@property
	def hash(self):
		return EosObject.object_to_hash(self)
	
	@staticmethod
	def object_to_hash(value):
		# TODO
		return 'DEADBEEF'
		#return base64.b64encode(hashlib.sha256(to_json(EosObject.serialise_and_wrap(value, None, True)).encode('utf-8')).digest())
	
	# TNYI: Transcrypt's handling of class methods is strange
	@classmethod
	def deserialise(cls, value):
		value = cls
		cls = this
		return cls._deserialise(cls, value)

# Stores information about a field of an EosObject for easy conversion to/from a Model
class EosField():
	def __init__(self, py_type, name=None, *, hashed=True, max_length=None, element_type=None, primary_key=False, editable=True, nullable=False, on_delete=None):
		self.name = name
		self.py_type = py_type
		self.hashed = hashed
		
		self.max_length = max_length
		self.element_type = element_type
		self.primary_key = primary_key
		self.editable = editable
		self.nullable = nullable # 'null' is a JS keyword
		self.on_delete = on_delete

class EosDictObjectType(EosObjectType):
	def __new__(meta, name, bases, attrs):
		meta, name, bases, attrs = EosDictObjectType._before_new(meta, name, bases, attrs)
		cls = EosObjectType.__new__(meta, name, bases, attrs)
		return cls
	
	def _before_new(meta, name, bases, attrs):
		return meta, name, bases, attrs

def testdecorator(f):
	if eos_core.is_python:
		def wrapper(*args, **kwargs):
			print('Hello World!')
		return wrapper
	return f

# Must declare eos_fields field
class EosDictObject(EosObject, metaclass=EosDictObjectType):
	class EosMeta:
		abstract = True
	
	def __init__(self, *args, **kwargs):
		# Emulate Django and set the fields
		#super().__init__()
		
		fields = [field.name for field in self._eosmeta.eos_fields]
		
		# We must handle both regular Python convention (kwargs) and Javascript-compatible syntax (args object)
		if len(args) == 1 and len(kwargs) == 0 and typeof(args[0]) == "object":
			# kwargs is always a JS object so this is okay
			kwargs = args.pop()
		
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
	
	@staticmethod
	def _deserialise(cls, value):
		result = {}
		for field in cls._eosmeta.eos_fields:
			result[field.name] = EosObject.deserialise_and_unwrap(value[field.name], field)
		return cls(**result)

def to_json(value):
	return eos_json.serialise(value)

def from_json(value):
	return JSON.parse(value)
