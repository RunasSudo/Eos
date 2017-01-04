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

from django.db import models

class ObjectField(models.Field):
	def __init__(self, field_type, *args, **kwargs):
		self.field_type = field_type
		super().__init__(*args, **kwargs)
	
	def deconstruct(self):
		name, path, args, kwargs = super().deconstruct()
		kwargs['field_type'] = self.field_type
		return name, path, args, kwargs
	
	def from_db_value(self, value, expression, connection, context):
		if value is None:
			return value
		return self.field_type.to_python(value)
	
	def to_python(self, value):
		if isinstance(value, self.field_type):
			return value
		if value is None:
			return value
		return self.field_type.to_python(value)
	
	def get_prep_value(self, value):
		return self.field_type.from_python(value)
	
	def get_internal_type(self):
		return self.field_type.__field_type__
