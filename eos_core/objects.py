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
	
	@staticmethod
	def get_all():
		import eos.settings
		import importlib
		for app in eos.settings.INSTALLED_APPS:
			try:
				importlib.import_module(app)
			except ImportError:
				pass
		return eos_objects
	
	@staticmethod
	def serialise_and_wrap(value, value_type):
		if value is None:
			return value
		if value_type is not None:
			# The value type is guaranteed, so store directly
			if issubclass(value_type, EosObject):
				return value.serialise()
			else:
				return value
		else:
			# The value type is unknown, so store wrapped
			if isinstance(value, EosObject):
				return { 'type': get_full_name(value), 'value': value.serialise() }
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
			if issubclass(value_type, EosObject):
				return value_type.deserialise(value)
			else:
				return value
		else:
			# The value type is unknown, so should be stored wrapped
			if value['type'] in eos_objects:
				return eos_objects[value['type']].deserialise(value['value'])
			else:
				return value['value']
	
	@staticmethod
	def deserialise_list(value, element_type):
		if value is None:
			return value
		return [EosObject.deserialise_and_unwrap(element, element_type) for element in value]

class EosDictObjectType(EosObjectType):
	def __call__(meta, *args, **kwargs):
		instance = super().__call__(*args, **kwargs)
		
		fields = [field for field, ftype in instance.eos_fields]
		for arg, val in kwargs:
			if arg in fields and not hasattr(instance, arg):
				setattr(instance, arg, val)
		
		return instance

# Must declare eos_fields field
class EosDictObject(EosObject, metaclass=EosDictObjectType):
	class Meta:
		abstract = True
	
	def serialise(self):
		result = {}
		for field in self.eos_fields:
			result[field[0]] = EosObject.serialise_and_wrap(getattr(self, field[0]), field[1])
		return result
	
	@classmethod
	def deserialise(cls, value):
		result = {}
		for field in cls.eos_fields:
			result[field[0]] = EosObject.deserialise_and_unwrap(value[field[0]], field[1])
		return cls(**result)
