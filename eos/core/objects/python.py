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

import mongoengine

class Field:
	def __init__(self, *args, **kwargs):
		if 'default' in kwargs:
			self.required = False
			self.default = kwargs['default']
		else:
			self.required = True
			self.default = None

class PrimitiveField(Field):
	def to_python(self):
		return self.mongo_field(
			required=self.required,
			default=self.default
		)

class StringField(PrimitiveField):
	mongo_field = mongoengine.StringField

class EosObjectType(type):
	def before_new(meta, name, bases, attrs):
		# Process fields
		fields = {}
		for attr, val in attrs.items():
			if isinstance(val, Field):
				fields[attr] = val
				attrs[attr] = val.to_python()
		attrs['_fields'] = fields
		
		return meta, name, bases, attrs

class TopLevelObjectType(mongoengine.base.TopLevelDocumentMetaclass, EosObjectType):
	def __new__(meta, name, bases, attrs):
		meta, name, bases, attrs = meta.before_new(meta, name, bases, attrs)
		return super().__new__(meta, name, bases, attrs)

class EmbeddedObjectType(mongoengine.base.DocumentMetaclass, EosObjectType):
	def __new__(meta, name, bases, attrs):
		meta, name, bases, attrs = meta.before_new(meta, name, bases, attrs)
		return super().__new__(meta, name, bases, attrs)

class EosObject():
	pass

class DocumentObject(EosObject):
	pass

class TopLevelObject(DocumentObject, mongoengine.Document, metaclass=TopLevelObjectType):
	meta = {
		'abstract': True
	}

class EmbeddedObject(DocumentObject, mongoengine.EmbeddedDocument, metaclass=EmbeddedObjectType):
	meta = {
		'abstract': True
	}
