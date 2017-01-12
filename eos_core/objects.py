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

import django.db.models

def get_full_name(obj):
	if isinstance(obj, type):
		return obj.__module__ + '.' + obj.__qualname__
	else:
		return type(obj).__module__ + '.' + type(obj).__qualname__

eos_objects = {}

class EosObjectType(type):
	def __new__(meta, name, bases, attrs):
		cls = super().__new__(meta, name, bases, attrs)
		
		# Meta will be automatically subclassed, but _meta will still point to the parent Meta class
		base_meta = getattr(cls, '_meta', None)
		attr_meta = attrs['Meta'] if 'Meta' in attrs else None
		if base_meta and getattr(base_meta, 'abstract', False) and not hasattr(attr_meta, 'abstract'):
			# Don't inherit the abstract field by default
			cls.Meta.abstract = False
		cls._meta = cls.Meta
		
		if not getattr(cls._meta, 'abstract', False):
			eos_objects[get_full_name(cls)] = cls
		
		return cls

# An object that can be serialised
class EosObject(metaclass=EosObjectType):
	class Meta:
		abstract = True
	
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
		return eos_objects
	
	@staticmethod
	def serialise_and_wrap(value, value_type):
		if value is None:
			return value
		if value_type is not None:
			# The value type is guaranteed, so store directly
			if issubclass(value_type.py_type, EosObject):
				return value.serialise()
			elif issubclass(value_type.py_type, list):
				return EosObject.serialise_list(value, value_type.element_type)
			else:
				return value
		else:
			# The value type is unknown, so store wrapped
			if isinstance(value, EosObject):
				return { 'type': get_full_name(value), 'value': value.serialise() }
			elif isinstance(value, list):
				return { 'type': get_full_name(value), 'value': EosObject.serialise_list(value, None) }
			else:
				return { 'type': get_full_name(value), 'value': value }
	
	@staticmethod
	def serialise_list(value, element_type):
		if value is None:
			return value
		return [EosObject.serialise_and_wrap(element, element_type) for element in value]
	
	@staticmethod
	def deserialise_and_unwrap(value, value_type):
		if value_type is not None:
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

# Stores information about a field of an EosObject for easy conversion to/from a Model
class EosField():
	def __init__(self, py_type, name=None, *, max_length=None, element_type=None):
		self.name = name
		self.py_type = py_type
		
		self.max_length = max_length
		self.element_type = element_type
	
	def create_django_field(self):
		if issubclass(self.py_type, EosObject):
			import eos_core.fields
			if self.py_type is EosObject:
				return eos_core.fields.EosObjectField()
			else:
				return eos_core.fields.EosObjectField(contained_type=self.py_type)
		if issubclass(self.py_type, int):
			return django.db.models.IntegerField()
		if issubclass(self.py_type, basestring):
			if self.max_length:
				return django.db.models.CharField(max_length=self.max_length)
			else:
				return django.db.models.TextField()
		if issubclass(self.py_type, list):
			return eos_core.fields.EosListField(element_type=self.element_type)
		raise Exception('Attempted to create Django field for unsupported Python type {}'.format(self.py_type))

class EosDictObjectType(EosObjectType):
	def __new__(meta, name, bases, attrs):
		cls = super().__new__(meta, name, bases, attrs)
		
		if eos_core.is_python and issubclass(cls, django.db.models.Model):
			for field in cls._meta.eos_fields:
				field.create_django_field().contribute_to_class(cls, field.name)
		
		return cls
	
	def __call__(meta, *args, **kwargs):
		#instance = super().__call__(*args, **kwargs)
		instance = super().__call__()
		
		if eos_core.is_python and isinstance(instance, django.db.models.Model):
			pass
		else:
			fields = [field.name for field in instance._meta.eos_fields]
			for arg in kwargs:
				if arg in fields and not hasattr(instance, arg):
					setattr(instance, arg, kwargs[arg])
		
		return instance

# Must declare eos_fields field
class EosDictObject(EosObject, metaclass=EosDictObjectType):
	class Meta:
		abstract = True
	
	def serialise(self):
		result = {}
		for field in self._meta.eos_fields:
			result[field.name] = EosObject.serialise_and_wrap(getattr(self, field.name), field)
		return result
	
	@classmethod
	def deserialise(cls, value):
		result = {}
		for field in cls._meta.eos_fields:
			result[field.name] = EosObject.deserialise_and_unwrap(value[field.name], field)
		return cls(**result)
