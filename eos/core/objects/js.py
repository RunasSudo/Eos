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

# Load json.js
lib = __pragma__('js', '''
(function() {{
	var exports = {{}};
	{}
	exports.stringify = stringify_main;
	return exports;
}})()''', __include__('eos/core/objects/json.js'))

# Fields
# ======

class Field:
	def __init__(self, *args, **kwargs):
		#console.log(kwargs.get('hashed', None))
		self.default = kwargs['py_default'] if kwargs.hasOwnProperty('py_default') else None
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
UUIDField = PrimitiveField # Different to Python

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

# Objects
# =======

class EosObjectType(type):
	def __new__(meta, name, bases, attrs):
		cls = type.__new__(meta, name, bases, attrs)
		cls._name = (meta.__next_class_module__ + '.' + cls.__name__).replace('.js.', '.') #TNYI: module and qualname
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
	
	@staticmethod
	def serialise_and_wrap(value, object_type=None):
		if object_type:
			return value.serialise()
		return {'type': value._name, 'value': value.serialise()}
	
	@staticmethod
	def deserialise_and_unwrap(value, object_type=None):
		if object_type:
			return object_type.deserialise(value)
		print(value['type'])
		return EosObject.objects[value['type']].deserialise(value['value'])
	
	# Different to Python
	@staticmethod
	def to_json(value):
		return lib.stringify(value)
	
	@staticmethod
	def from_json(value):
		return JSON.parse(value)

class EosList(EosObject):
	def __init__(self, *args):
		self.impl = list(*args)
	
	# Diferent to Python
	# Lists are implemented as native JS Arrays, so no cheating here :(
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
		fields = Object.create(cls._fields) if hasattr(cls, '_fields') else {} # Different to Python: TNYI dict.copy not implemented
		for attr in list(dir(cls)):
			val = getattr(cls, attr)
			if isinstance(val, Field):
				val._instance = (cls, name)
				fields[attr] = val
				delattr(cls, attr)
		cls._fields = fields
		
		# Make properties
		# Different to Python: This is handled at the instance level
		
		return cls

class DocumentObject(EosObject, metaclass=DocumentObjectType):
	_ver = StringField(default='0.1')
	
	def __init__(self, *args, **kwargs):
		super().__init__()
		
		self._field_values = {}
		
		# Different to Python
		for attr, val in self._fields.items():
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
	
	# Different to Python
	# TNYI: Strange things happen with py_ attributes
	def serialise(self):
		return {(attr[3:] if attr.startswith('py_') else attr): val.serialise(getattr(self, attr)) for attr, val in self._fields.items()}
	
	@classmethod
	def deserialise(cls, value):
		return cls(**{attr: val.deserialise(value[attr[3:] if attr.startswith('py_') else attr]) for attr, val in cls._fields.items()})

class TopLevelObject(DocumentObject):
	pass

class EmbeddedObject(DocumentObject):
	pass
