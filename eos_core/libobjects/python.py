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
import eos_core.hashing

import django.db.models
import django.utils.timezone

import datetime as datetime_module
import json
import uuid as uuid_module

datetime = datetime_module.datetime
uuid = uuid_module.UUID

def get_full_name(obj):
	if not isinstance(obj, type): # an instance instead of a class
		obj = type(obj)
	
	if obj.__module__ == '__fake__':
		# For Django migrations, the name is not important
		return obj.__module__ + '.' + obj.__name__
	if obj.__module__ == 'builtins':
		return obj.__module__ + '.' + obj.__name__
	if hasattr(obj._eosmeta, 'eos_name'):
		return obj._eosmeta.eos_name
	
	raise Exception('Unknown full name for object ' + obj.__name__ + '; suggesting ' + obj.__module__ + '.' + obj.__name__)

class EosObjectType(type):
	def __new__(meta, name, bases, attrs):
		cls = super().__new__(meta, name, bases, attrs)
		cls = EosObjectType._after_new(cls, meta, name, bases, attrs)
		return cls
	
	def _after_new(cls, meta, name, bases, attrs):
		# Meta will be automatically subclassed, but _meta will still point to the parent Meta class
		base_meta = getattr(cls, '_eosmeta', None)
		attr_meta = attrs['EosMeta'] if 'EosMeta' in attrs else None
		if base_meta and getattr(base_meta, 'abstract', False) and not hasattr(attr_meta, 'abstract'):
			# Don't inherit the abstract field by default
			cls.EosMeta.abstract = False
		cls._eosmeta = cls.EosMeta
		
		if not getattr(cls._eosmeta, 'abstract', False):
			eos_core.libobjects.eos_objects[get_full_name(cls)] = cls
		
		return cls

# An object that can be serialised
class EosObject(metaclass=EosObjectType):
	class EosMeta:
		abstract = True
	
	def __str__(self):
		return eos_core.libobjects.to_json(EosObject.serialise_and_wrap(self, None))
	
	def __eq__(self, other):
		return (get_full_name(self) == get_full_name(other)) and (self.serialise() == other.serialise())
	
	@staticmethod
	def get_all():
		import eos.settings
		import importlib
		for app in eos.settings.INSTALLED_APPS:
			try:
				importlib.import_module(app + '.objects')
			except ImportError:
				pass
		return eos_core.libobjects.eos_objects
	
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
			elif issubclass(value_type.py_type, uuid):
				return str(value)
			elif issubclass(value_type.py_type, datetime):
				return value.astimezone(django.utils.timezone.utc).isoformat()
			else:
				return value
		else:
			# The value type is unknown, so store wrapped
			if isinstance(value, EosObject):
				return { 'type': get_full_name(value), 'value': value.serialise(hashed) }
			elif isinstance(value, list):
				return { 'type': get_full_name(value), 'value': EosObject.serialise_list(value, None, hashed) }
			elif isinstance(value, uuid):
				return { 'type': get_full_name(value), 'value': str(value) }
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
			if value['type'] in EosObject.get_all():
				return EosObject.get_all()[value['type']].deserialise(value['value'])
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
		return eos_core.libobjects.EosObject.object_to_hash(self)
	
	@staticmethod
	def object_to_hash(value):
		return eos_core.hashing.hash_as_b64(eos_core.libobjects.to_json(EosObject.serialise_and_wrap(value, None, True)))
	
	@classmethod
	def deserialise(cls, value):
		return cls._deserialise(cls, value)

# Stores information about a field of an EosObject for easy conversion to/from a Model
class EosField():
	def __init__(self, py_type, name=None, *, serialised=True, hashed=True, linked_property=None, max_length=None, element_type=None, primary_key=False, editable=True, nullable=False, on_delete=None):
		self.name = name
		self.py_type = py_type
		self.serialised = serialised
		self.hashed = hashed
		self.linked_property = linked_property
		
		self.max_length = max_length
		self.element_type = element_type
		self.primary_key = primary_key
		self.editable = editable
		self.null = nullable # 'null' is a JS keyword
		self.on_delete = on_delete
	
	def __repr__(self):
		return self.name
	
	def create_django_field(self):
		general_keys = {x: getattr(self, x) for x in ['primary_key', 'editable', 'null']}
		
		if self.linked_property:
			# This is not actually a field!
			def get_that_property(obj):
				val = getattr(obj, self.linked_property)
				if val.__class__.__name__ == 'RelatedManager':
					if hasattr(val, 'select_subclasses'):
						return val.select_subclasses()
					return val.all()
				return val
			return property(get_that_property)
		
		if isinstance(self.py_type, type):
			if issubclass(self.py_type, EosObject):
				import eos_core.fields
				if issubclass(self.py_type, django.db.models.Model):
					return django.db.models.ForeignKey(self.py_type._meta.app_label + '.' + self.py_type._meta.object_name)
				elif self.py_type is EosObject:
					return eos_core.fields.EosObjectField(**general_keys)
				else:
					return eos_core.fields.EosObjectField(py_type=self.py_type, **general_keys)
			if issubclass(self.py_type, int):
				return django.db.models.IntegerField(**general_keys)
			if issubclass(self.py_type, str):
				if self.max_length:
					return django.db.models.CharField(max_length=self.max_length, **general_keys)
				else:
					return django.db.models.TextField(**general_keys)
			if issubclass(self.py_type, list):
				import eos_core.fields
				return eos_core.fields.EosListField(element_type=self.element_type, **general_keys)
		if isinstance(self.py_type, str):
			return django.db.models.ForeignKey(self.py_type, on_delete=getattr(django.db.models, self.on_delete), **general_keys)
		if self.py_type is uuid:
			return django.db.models.UUIDField(default=uuid_module.uuid4, **general_keys)
		if self.py_type is datetime:
			return django.db.models.DateTimeField(**general_keys)
		raise Exception('Attempted to create Django field for unsupported Python type {}'.format(self.py_type))

class EosDictObjectType(EosObjectType):
	def __new__(meta, name, bases, attrs):
		meta, name, bases, attrs = EosDictObjectType._before_new(meta, name, bases, attrs)
		cls = super().__new__(meta, name, bases, attrs)
		return cls
	
	def _before_new(meta, name, bases, attrs):
		if eos_core.is_python and any(issubclass(base, django.db.models.Model) for base in bases):
			# Set up some defaults
			if 'EosMeta' not in attrs:
				class EosMeta:
					eos_fields = []
				attrs['EosMeta'] = EosMeta
			if not hasattr(attrs['EosMeta'], 'eos_fields'):
				# Try to inherit fields
				try:
					attrs['EosMeta'].eos_fields = next(base for base in bases if issubclass(base, EosDictObject))._eosmeta.eos_fields
				except StopIteration:
					pass
			
			for field in attrs['EosMeta'].eos_fields:
				if not any(hasattr(base, field.name) for base in bases):
					attrs[field.name] = field.create_django_field()
		
		return meta, name, bases, attrs

class EosDictObject(EosObject, metaclass=EosDictObjectType):
	class EosMeta:
		abstract = True
		eos_fields = []
	
	def __init__(self, *args, **kwargs):
		if isinstance(self, django.db.models.Model):
			# Allow Django to manage setup
			super().__init__(*args, **kwargs)
		else:
			# Emulate Django and set the fields
			#super().__init__()
			
			fields = [field.name for field in self._eosmeta.eos_fields]
			for arg in kwargs:
				if arg in fields and not hasattr(self, arg):
					setattr(self, arg, kwargs[arg])
	
	def serialise(self, hashed=False):
		result = {}
		for field in self._eosmeta.eos_fields:
			if field.serialised and (not hashed or field.hashed):
				result[field.name] = EosObject.serialise_and_wrap(getattr(self, field.name), field, hashed)
		return result
	
	@staticmethod
	def _deserialise(cls, value):
		result = {}
		for field in cls._eosmeta.eos_fields:
			result[field.name] = EosObject.deserialise_and_unwrap(value[field.name], field)
		return cls(**result)

def to_json(value):
	return json.dumps(value, sort_keys=True)

def from_json(value):
	return json.loads(value)
