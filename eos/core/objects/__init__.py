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

if is_python:
	__pragma__('skip')
	import pymongo
	from bson.binary import UUIDLegacy
	
	import base64
	import hashlib
	import json
	import uuid
	__pragma__('noskip')
else:
	# Load json.js, jssha-sha256.js
	lib = __pragma__('js', '''
	(function() {{
		{}
		{}
		var exports = {{}};
		exports.stringify = stringify_main;
		exports.jsSHA = window.jsSHA;
		return exports;
	}})()''', __include__('eos/core/objects/json.js'), __include__('eos/core/objects/jssha-sha256.js'))

# Database
# ========

if is_python:
	client = pymongo.MongoClient()
	db = client['test']

# Fields
# ======

class Field:
	def __init__(self, *args, **kwargs):
		self.default = kwargs.get('default', kwargs.get('py_default', None))
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
		super().__init__(default=EosList, *args, **kwargs)
		self.element_field = element_field
	
	def serialise(self, value):
		return [self.element_field.serialise(x) for x in value]
	
	def deserialise(self, value):
		return [self.element_field.deserialise(x) for x in value]

class EmbeddedObjectListField(Field):
	def __init__(self, object_type=None, *args, **kwargs):
		super().__init__(default=EosList, *args, **kwargs)
		self.object_type = object_type
	
	def serialise(self, value):
		return [EosObject.serialise_and_wrap(x, self.object_type) for x in value]
	
	def deserialise(self, value):
		return [EosObject.deserialise_and_unwrap(x, self.object_type) for x in value]

if is_python:
	class UUIDField(Field):
		def __init__(self, *args, **kwargs):
			super().__init__(default=uuid.uuid4, *args, **kwargs)
		
		def serialise(self, value):
			return str(value)
		
		def deserialise(self, value):
			return uuid.UUID(value)
else:
	UUIDField = PrimitiveField

# Objects
# =======

class EosObjectType(type):
	def __new__(meta, name, bases, attrs):
		cls = type.__new__(meta, name, bases, attrs)
		cls._name = ((cls.__module__ if is_python else meta.__next_class_module__) + '.' + cls.__name__).replace('.js.', '.').replace('.python.', '.') #TNYI: module and qualname
		if name != 'EosObject':
			EosObject.objects[cls._name] = cls
		return cls

class EosObject(metaclass=EosObjectType):
	objects = {}
	
	def __init__(self):
		self._instance = (None, None)
		self._inited = False
	
	def post_init(self):
		self._inited = True
	
	def recurse_parents(self, cls):
		if isinstance(self, cls):
			return self
		if self._instance[0]:
			return self._instance[0].recurse_parents(cls)
		return None
	
	@property
	def hash(self):
		return EosObject.to_sha256(EosObject.serialise_and_wrap(self))
	
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
	
	@staticmethod
	def to_sha256(value):
		if is_python:
			sha_obj = hashlib.sha256()
			sha_obj.update(value.encode('utf-8'))
			return base64.b64encode(sha_obj.digest()).decode('utf-8')
		else:
			# TNYI: This is completely borked
			sha_obj = __pragma__('js', '{}', 'new lib.jsSHA("SHA-256", "TEXT")')
			sha_obj.js_update(value)
			return sha_obj.getHash('B64')

class EosList(EosObject):
	def __init__(self, *args):
		super().__init__()
		
		self.impl = list(*args)
	
	# Lists in JS are implemented as native Arrays, so no cheating here :(
	def __len__(self):
		return len(self.impl)
	def __getitem__(self, idx):
		return self.impl[idx]
	def __setitem__(self, idx, val):
		self.impl[idx] = val
	def __contains__(self, val):
		return val in self.impl
	
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
				fields[attr] = val
				delattr(cls, attr)
		cls._fields = fields
		
		# Make properties
		if is_python:
			def make_property(name, field):
				def field_getter(self):
					return self._field_values[name]
				def field_setter(self, value):
					if isinstance(value, EosObject):
						value._instance = (self, name)
						if not value._inited:
							value.post_init()
					
					self._field_values[name] = value
				return property(field_getter, field_setter)
			
			for attr, val in fields.items():
				setattr(cls, attr, make_property(attr, val))
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
						if isinstance(value, EosObject):
							value._instance = (self, name)
							if not value._inited:
								value.post_init()
						
						self._field_values[name] = value
					return (field_getter, field_setter)
				prop = make_property(attr, val)
				# TNYI: No support for property()
				Object.defineProperty(self, attr, {
					'get': prop[0],
					'set': prop[1]
				})
			
			if attr in kwargs:
				setattr(self, attr, kwargs[attr])
			else:
				default = val.default
				if default is not None and callable(default):
					default = default()
				setattr(self, attr, default)
	
	# TNYI: Strange things happen with py_ attributes
	def serialise(self):
		return {(attr[3:] if attr.startswith('py_') else attr): val.serialise(getattr(self, attr)) for attr, val in self._fields.items()}
	
	@classmethod
	def deserialise(cls, value):
		return cls(**{attr: val.deserialise(value[attr[3:] if attr.startswith('py_') else attr]) for attr, val in cls._fields.items()})

class TopLevelObject(DocumentObject):
	def save(self):
		#res = db[self._name].replace_one({'_id': self.serialise()['_id']}, self.serialise(), upsert=True)
		res = db[self._name].replace_one({'_id': self._fields['_id'].serialise(self._id)}, EosObject.serialise_and_wrap(self), upsert=True)

class EmbeddedObject(DocumentObject):
	pass
