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

import django.db.models

# Django field which stores a serialised object
class EosObjectField(django.db.models.Field):
	def __init__(self, py_type=None, *args, **kwargs):
		self.field_type = None if py_type is None else eos_core.libobjects.EosField(py_type)
		super().__init__(*args, **kwargs)
	
	def deconstruct(self):
		name, path, args, kwargs = super().deconstruct()
		kwargs['py_type'] = None if self.field_type is None else self.field_type.py_type
		return name, path, args, kwargs
	
	def from_db_value(self, value, expression, connection, context):
		return self.to_python(value)
	
	def to_python(self, value):
		if isinstance(value, eos_core.libobjects.EosObject):
			return value
		if value is None:
			return value
		if value == 'null':
			return None
		return eos_core.libobjects.EosObject.deserialise_and_unwrap(eos_core.libobjects.from_json(value), self.field_type)
	
	def get_prep_value(self, value):
		if isinstance(value, str):
		#	if value == '':
		#		return 'null'
			return value
		return eos_core.libobjects.to_json(eos_core.libobjects.EosObject.serialise_and_wrap(value, self.field_type))
	
	def get_internal_type(self):
		return 'TextField'

class EosListField(django.db.models.Field):
	def __init__(self, element_type=None, *args, **kwargs):
		self.element_type = element_type
		super().__init__(*args, **kwargs)
	
	def deconstruct(self):
		name, path, args, kwargs = super().deconstruct()
		kwargs['element_type'] = self.element_type
		return name, path, args, kwargs
	
	def from_db_value(self, value, expression, connection, context):
		return self.to_python(value)
	
	def to_python(self, value):
		if isinstance(value, list):
			return value
		if value is None:
			return value
		return eos_core.libobjects.EosObject.deserialise_list(eos_core.libobjects.from_json(value), self.element_type)
	
	def get_prep_value(self, value):
		return eos_core.libobjects.to_json(eos_core.libobjects.EosObject.serialise_list(value, self.element_type))
	
	def get_internal_type(self):
		return 'TextField'
