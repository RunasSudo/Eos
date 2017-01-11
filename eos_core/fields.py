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

import eos_core.objects

import django.db.models

import json

# Django field which stores a serialised object
class EosObjectField(django.db.models.Field):
	def __init__(self, field_type=None, *args, **kwargs):
		self.field_type = field_type
		super().__init__(*args, **kwargs)
	
	def deconstruct(self):
		name, path, args, kwargs = super().deconstruct()
		kwargs['field_type'] = self.field_type
		return name, path, args, kwargs
	
	def from_db_value(self, value, expression, connection, context):
		return self.to_python(value)
	
	def to_python(self, value):
		if isinstance(value, EosObject):
			return value
		return eos_core.objects.EosObject.deserialise_and_unwrap(json.loads(value), self.field_type)
	
	def get_prep_value(self, value):
		return json.dumps(eos_core.objects.EosObject.serialise_and_wrap(value, self.field_type))
	
	def get_internal_type(self):
		return self.field_type.__field_type__

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
		return eos_core.objects.EosObject.deserialise_list(json.loads(value), self.element_type)
	
	def get_prep_value(self, value):
		return json.dumps(eos_core.objects.EosObject.serialise_list(value, self.element_type))
	
	def get_internal_type(self):
		return 'TextField'
