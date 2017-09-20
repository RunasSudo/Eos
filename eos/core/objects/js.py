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

class Field:
	def __init__(self, *args, **kwargs):
		if 'default' in kwargs:
			self.required = False
			self.default = kwargs['default']
		else:
			self.required = True
			self.default = None

StringField = Field

class EosObjectType(type):
	def before_new(meta, name, bases, attrs):
		# Process fields
		fields = {}
		for attr, val in dict(attrs).items():
			if isinstance(val, Field):
				fields[attr] = val
				attrs[attr] = val.to_python()
		attrs['_fields'] = fields
		
		return meta, name, bases, attrs
	
	def __new__(meta, name, bases, attrs):
		meta, name, bases, attrs = meta.before_new(meta, name, bases, attrs)
		#return super().__new__(meta, name, bases, attrs)
		return type.__new__(meta, name, bases, attrs)

class EosObject():
	pass

class DocumentObject(EosObject, metaclass=EosObjectType):
	def __init__(self, *args, **kwargs):
		# Process fields
		for name, field in self._fields.items():
			if name not in kwargs:
				continue
			setattr(self, name, kwargs.pop(name, field.default))

# MongoDB distinguishes between these two, but we don't care
TopLevelObject = DocumentObject
EmbeddedObject = DocumentObject
