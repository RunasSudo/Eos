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

# Libraries
# =========

import eos.core.db

if is_python:
	__pragma__('skip')
	import eos.core.db.mongodb
	import eos.core.db.postgresql
	
	from bson.binary import UUIDLegacy
	
	import base64
	from datetime import datetime
	import hashlib
	import json
	import uuid
	__pragma__('noskip')
else:
	# Load json.js
	lib = __pragma__('js', '''
	(function() {{
		{}
		var exports = {{}};
		exports.stringify = stringify_main;
		return exports;
	}})()''', __include__('eos/core/objects/json.js'))

# Database
# ========

class DBInfo:
	def __init__(self):
		self.provider = eos.core.db.DummyProvider(None, None)

dbinfo = DBInfo()

def db_connect(db_name, db_uri='mongodb://localhost:27017/', db_type='mongodb'):
	dbinfo.provider = eos.core.db.db_providers[db_type](db_name, db_uri)
	dbinfo.provider.connect()

# Fields
# ======

class Field:
	def __init__(self, *args, **kwargs):
		self.default = kwargs['default'] if 'default' in kwargs else kwargs['py_default'] if 'py_default' in kwargs else None
		self.is_protected = kwargs['is_protected'] if 'is_protected' in kwargs else False
		self.is_hashed = kwargs['is_hashed'] if 'is_hashed' in kwargs else not self.is_protected

class PrimitiveField(Field):
	def serialise(self, value, for_hash=False, should_protect=False):
		return value
	
	def deserialise(self, value):
		return value

DictField = PrimitiveField
IntField = PrimitiveField
StringField = PrimitiveField

class EmbeddedObjectField(Field):
	def __init__(self, object_type=None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.object_type = object_type
	
	def serialise(self, value, for_hash=False, should_protect=False):
		return EosObject.serialise_and_wrap(value, self.object_type, for_hash, should_protect)
	
	def deserialise(self, value):
		return EosObject.deserialise_and_unwrap(value, self.object_type)

class ListField(Field):
	def __init__(self, element_field=None, *args, **kwargs):
		super().__init__(default=EosList, *args, **kwargs)
		self.element_field = element_field
	
	def serialise(self, value, for_hash=False, should_protect=False):
		return [self.element_field.serialise(x, for_hash, should_protect) for x in (value.impl if isinstance(value, EosList) else value)]
	
	def deserialise(self, value):
		return EosList([self.element_field.deserialise(x) for x in value])

class EmbeddedObjectListField(Field):
	def __init__(self, object_type=None, *args, **kwargs):
		super().__init__(default=EosList, *args, **kwargs)
		self.object_type = object_type
	
	def serialise(self, value, for_hash=False, should_protect=False):
		# TNYI: Doesn't know how to deal with iterators like EosList
		if value is None:
			return None
		return [EosObject.serialise_and_wrap(x, self.object_type, for_hash, should_protect) for x in (value.impl if isinstance(value, EosList) else value)]
	
	def deserialise(self, value):
		if value is None:
			return None
		return EosList([EosObject.deserialise_and_unwrap(x, self.object_type) for x in value])

if is_python:
	class UUIDField(Field):
		def __init__(self, *args, **kwargs):
			super().__init__(default=uuid.uuid4, *args, **kwargs)
		
		def serialise(self, value, for_hash=False, should_protect=False):
			return str(value)
		
		def deserialise(self, value):
			return uuid.UUID(value)
else:
	UUIDField = PrimitiveField

class DateTimeField(Field):
	def pad(self, number):
		if number < 10:
			return '0' + str(number)
		return str(number)
	
	def serialise(self, value, for_hash=False, should_protect=False):
		if value is None:
			return None
		
		if is_python:
			return value.strftime('%Y-%m-%dT%H:%M:%SZ')
		else:
			return value.getUTCFullYear() + '-' + self.pad(value.getUTCMonth() + 1) + '-' + self.pad(value.getUTCDate()) + 'T' + self.pad(value.getUTCHours()) + ':' + self.pad(value.getUTCMinutes()) + ':' + self.pad(value.getUTCSeconds()) + 'Z'
	
	def deserialise(self, value):
		if value is None:
			return None
		
		if is_python:
			return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
		else:
			return __pragma__('js', '{}', 'new Date(value)')
	
	@staticmethod
	def now():
		if is_python:
			return datetime.utcnow()
		else:
			return __pragma__('js', '{}', 'new Date()')

# Objects
# =======

class EosObjectType(type):
	def __new__(meta, name, bases, attrs):
		cls = type.__new__(meta, name, bases, attrs)
		cls._name = (cls.__module__ + '.' + cls.__name__).replace('.js.', '.').replace('.python.', '.') #TNYI: qualname
		if name != 'EosObject':
			EosObject.objects[cls._name] = cls
		if '_db_name' not in attrs:
			# Don't inherit _db_name, use only if explicitly given
			cls._db_name = cls._name
		return cls

class EosObject(metaclass=EosObjectType):
	objects = {}
	
	def __init__(self):
		self._instance = (None, None)
		self._inited = False
	
	def post_init(self):
		self._inited = True
	
	def recurse_parents(self, cls):
		#if not isinstance(cls, type):
		if isinstance(cls, str):
			cls = EosObject.objects[cls]
		
		if isinstance(self, cls):
			return self
		if self._instance[0]:
			return self._instance[0].recurse_parents(cls)
		return None
	
	def __eq__(self, other):
		if not isinstance(other, EosObject):
			return False
		return EosObject.serialise_and_wrap(self) == EosObject.serialise_and_wrap(other)
	
	@staticmethod
	def serialise_and_wrap(value, object_type=None, for_hash=False, should_protect=False):
		if object_type:
			if value:
				return value.serialise(for_hash, should_protect)
			return None
		return {'type': value._name, 'value': (value.serialise(for_hash, should_protect) if value else None)}
	
	@staticmethod
	def deserialise_and_unwrap(value, object_type=None):
		if object_type:
			return object_type.deserialise(value)
		return EosObject.objects[value['type']].deserialise(value['value'])
	
	@staticmethod
	def to_json(value):
		if is_python:
			return json.dumps(value, sort_keys=True)
		else:
			return lib.stringify(value)
	
	@staticmethod
	def from_json(value):
		if is_python:
			return json.loads(value)
		else:
			return JSON.parse(value)

class EosList(EosObject):
	def __init__(self, *args):
		super().__init__()
		
		self.impl = list(*args)
	
	def post_init(self):
		for i in range(len(self.impl)):
			val = self.impl[i]
			# Check if object has writeable attributes
			if is_python and hasattr(val, '__dict__'):
				val._instance = (self, i)
				if not val._inited:
					val.post_init()
	
	def __repr__(self):
		return '<EosList {}>'.format(repr(self.impl))
	
	# Lists in JS are implemented as native Arrays, so no cheating here :(
	def __len__(self):
		return len(self.impl)
	def __getitem__(self, idx):
		return self.impl[idx]
	def __setitem__(self, idx, val):
		self.impl[idx] = val
		val._instance = (self, idx)
		if not val._inited:
			val.post_init()
	def __contains__(self, val):
		return val in self.impl
	
	# For sorting, etc.
	def __eq__(self, other):
		if isinstance(other, EosList):
			other = other.impl
		return self.impl == other
	def __lt__(self, other):
		if isinstance(other, EosList):
			other = other.impl
		return self.impl < other
	
	def append(self, value):
		if isinstance(value, EosObject):
			value._instance = (self, len(self))
			if not value._inited:
				value.post_init()
		return self.impl.append(value)

class DocumentObjectType(EosObjectType):
	def __new__(meta, name, bases, attrs):
		cls = EosObjectType.__new__(meta, name, bases, attrs)
		
		# Process fields
		fields = {}
		if hasattr(cls, '_fields'):
			fields = cls._fields.copy() if is_python else Object.create(cls._fields)
		for attr in list(dir(cls)):
			if not is_python:
				# We must skip things with getters or else they will be called here (too soon)
				if Object.getOwnPropertyDescriptor(cls, attr).js_get:
					continue
			
			val = getattr(cls, attr)
			if isinstance(val, Field):
				val._instance = (cls, name)
				
				# Transcrypt does funky things with aliases, which are usually helpful, but not here
				if not is_python and attr.startswith('py_'):
					real_attr = attr[3:]
				else:
					real_attr = attr
				
				val.real_name = real_attr # The JSON/Python name
				val.internal_name = attr # The name that gets passed in as kwargs in Javascript
				
				fields[real_attr] = val
				delattr(cls, attr)
		cls._fields = fields
		
		# Make properties
		if is_python:
			def make_property(name, field):
				def field_getter(self):
					return self._field_values[name]
				def field_setter(self, value):
					self._field_values[name] = value
					
					if isinstance(value, EosObject):
						value._instance = (self, name)
						if not value._inited:
							value.post_init()
				return property(field_getter, field_setter)
			
			for attr, val in fields.items():
				setattr(cls, val.real_name, make_property(val.real_name, val))
				#if val.real_name != val.internal_name:
				#	setattr(cls, val.internal_name, make_property(val.real_name, val))
		else:
			# Handled at instance level
			pass
		
		return cls

class DocumentObject(EosObject, metaclass=DocumentObjectType):
	_ver = StringField(default='0.1')
	
	def __init__(self, *args, **kwargs):
		super().__init__()
		
		self._field_values = {}
		
		# Different to Python
		for attr, val in self._fields.items():
			if is_python:
				# Properties handled above
				pass
			else:
				def make_property(name, field):
					def field_getter():
						return self._field_values[name]
					def field_setter(value):
						self._field_values[name] = value
						
						if isinstance(value, EosObject):
							value._instance = (self, name)
							if not value._inited:
								value.post_init()
					return (field_getter, field_setter)
				prop = make_property(val.real_name, val)
				# TNYI: No support for property()
				Object.defineProperty(self, val.real_name, {
					'get': prop[0],
					'set': prop[1]
				})
				if val.real_name != val.internal_name:
					# Allow reference as e.g. both obj.py_name (from Python code) and obj.name (from JS templates)
					Object.defineProperty(self, val.internal_name, {
						'get': prop[0],
						'set': prop[1]
					})
			
			if val.internal_name in kwargs:
				setattr(self, val.real_name, kwargs[val.internal_name])
			else:
				default = val.default
				if default is not None and callable(default):
					default = default()
				setattr(self, val.real_name, default)
	
	def serialise(self, for_hash=False, should_protect=False):
		return {val.real_name: val.serialise(getattr(self, val.real_name), for_hash, should_protect) for attr, val in self._fields.items() if ((val.is_hashed or not for_hash) and (not should_protect or not val.is_protected))}
	
	@classmethod
	def deserialise(cls, value):
		if value is None:
			return None
		
		attrs = {}
		for attr, val in cls._fields.items():
			if attr in value:
				attrs[val.internal_name] = val.deserialise(value[val.real_name])
		return cls(**attrs)

class TopLevelObject(DocumentObject):
	def save(self):
		#res = db[self._name].replace_one({'_id': self.serialise()['_id']}, self.serialise(), upsert=True)
		#res = dbinfo.db[self._db_name].replace_one({'_id': self._fields['_id'].serialise(self._id)}, EosObject.serialise_and_wrap(self), upsert=True)
		dbinfo.provider.update_by_id(self._db_name, self._fields['_id'].serialise(self._id), EosObject.serialise_and_wrap(self))
	
	@classmethod
	def get_all(cls):
		return [EosObject.deserialise_and_unwrap(x) for x in dbinfo.provider.get_all(cls._db_name)]
	
	@classmethod
	def get_by_id(cls, _id):
		return EosObject.deserialise_and_unwrap(dbinfo.provider.get_by_id(cls._db_name, _id))

class EmbeddedObject(DocumentObject):
	pass
