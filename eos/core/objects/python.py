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
from bson.binary import UUIDLegacy

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
		return EosObject.serialise_and_wrap(value, self.object_type)
	
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

class EmbeddedObjectListField(Field):
	def __init__(self, object_type=None, *args, **kwargs):
		super().__init__(default=[], *args, **kwargs)
		self.object_type = object_type
	
	def serialise(self, value):
		return [EosObject.serialise_and_wrap(x, self.object_type) for x in value]
	
	def deserialise(self, value):
		return [EosObject.deserialise_and_unwrap(x, self.object_type) for x in value]

class UUIDField(Field):
	def __init__(self, *args, **kwargs):
		super().__init__(default=uuid.uuid4, *args, **kwargs)
	
	def serialise(self, value):
		return str(value)
	
	def unserialise(self, value):
		return uuid.UUID(value)

# Objects
# =======

class EosObjectType(type):
	def __new__(meta, name, bases, attrs):
		cls = type.__new__(meta, name, bases, attrs)
		cls._name = cls.__module__ + '.' + cls.__qualname__
		if name != 'EosObject':
			EosObject.objects[cls._name] = cls
		return cls

class EosObject(metaclass=EosObjectType):
	objects = {}
	
	@staticmethod
	def serialise_and_wrap(value, object_type=None):
		if object_type:
			return value.serialise()
		return {'type': value._name, 'value': value.serialise()}
	
	@staticmethod
	def deserialise_and_unwrap(value, object_type=None):
		if object_type:
			return object_type.deserialise(value)
		return EosObject.objects[value['type']].deserialise(value['value'])

class DocumentObjectType(EosObjectType):
	def __new__(meta, name, bases, attrs):
		cls = EosObjectType.__new__(meta, name, bases, attrs)
		
		# Process fields
		fields = cls._fields.copy() if hasattr(cls, '_fields') else {} # remember to .copy() XD
		for attr in list(dir(cls)):
			val = getattr(cls, attr)
			if isinstance(val, Field):
				fields[attr] = val
				delattr(cls, attr)
		cls._fields = fields
		
		return cls

class DocumentObject(metaclass=DocumentObjectType):
	def __init__(self, *args, **kwargs):
		for attr, val in self._fields.items():
			if attr in kwargs:
				setattr(self, attr, kwargs[attr])
			else:
				default = val.default
				if callable(default):
					default = default()
				setattr(self, attr, default)
	
	def serialise(self):
		return {attr: val.serialise(getattr(self, attr)) for attr, val in self._fields.items()}
	
	@classmethod
	def deserialise(cls, value):
		return cls(**value) # wew

class TopLevelObject(DocumentObject):
	def save(self):
		res = db[self._name].replace_one({'_id': self.serialise()['_id']}, self.serialise(), upsert=True)

class EmbeddedObject(DocumentObject):
	pass
