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

import pymongo

import uuid

# Database
# ========

client = pymongo.MongoClient()
db = client['test']

# Fields
# ======

class Field:
	def __init__(self, *args, **kwargs):
		self.default = kwargs.get('default', None)
		self.hashed = kwargs.get('hashed', True)

class PrimitiveField(Field):
	def serialise(self, value):
		return value
	
	def deserialise(self, value):
		return value

DictField = PrimitiveField
IntField = PrimitiveField
ListField = PrimitiveField
StringField = PrimitiveField

class EmbeddedObjectField(Field):
	def __init__(self, object_type=None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.object_type = object_type
	
	def serialise(self, value):
		return value.serialise_and_wrap(self.object_type)
	
	def deserialise(self, value):
		return EosObject.deserialise_and_unwrap(value, self.object_type)

class ListField(Field):
	def __init__(self, element_field=None, *args, **kwargs):
		super().__init__(default=[], *args, **kwargs)
		self.element_field = element_field
	
	def serialise(self, value):
		return [self.element_field.serialise(x) for x in value]
	
	def deserialise(self, value):
		return [self.element_field.deserialise(x) for x in value]

EmbeddedObjectListField = ListField

class UUIDField(Field):
	def __init__(self, *args, **kwargs):
		super().__init__(default=uuid.uuid4, *args, **kwargs)
	
	def serialise(self, value):
		return str(uuid.uuid4)
	
	def unserialise(self, value):
		return uuid.uuid4(value)

# Objects
# =======

class EosObjectType(type):
	def __new__(meta, name, bases, attrs):
		#meta, name, bases, attrs = meta.before_new(meta, name, bases, attrs)
		cls = type.__new__(meta, name, bases, attrs)
		
		# Process fields
		fields = cls._fields if hasattr(cls, '_fields') else {}
		for attr in list(dir(cls)):
			val = getattr(cls, attr)
			if isinstance(val, Field):
				fields[attr] = val
				delattr(cls, attr)
		cls._fields = fields
		
		cls._name = cls.__module__ + '.' + cls.__qualname__
		
		return cls

class EosObject(metaclass=EosObjectType):
	def __init__(self, *args, **kwargs):
		for attr, val in self._fields.items():
			setattr(self, attr, kwargs.get(attr, val.default))

TopLevelObject = EosObject
EmbeddedObject = EosObject
