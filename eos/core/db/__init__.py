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

db_providers = {}

class DBProvider:
	def __init__(self, db_name, db_uri):
		self.db_name = db_name
		self.db_uri = db_uri
	
	def connect(self):
		raise Exception('Not implemented')
	
	def get_all(self, collection):
		raise Exception('Not implemented')
	
	def get_all_by_fields(self, collection, fields):
		raise Exception('Not implemented')
	
	def get_by_id(self, collection, _id):
		raise Exception('Not implemented')
	
	def update_by_id(self, collection, _id, value):
		raise Exception('Not implemented')
	
	def delete_by_id(self, collection, _id):
		raise Exception('Not implemented')
	
	def reset_db(self):
		raise Exception('Not implemented')

class DummyProvider(DBProvider):
	def connect(self):
		pass
	
	def get_all(self, collection):
		pass
	
	def get_all_by_fields(self, collection, fields):
		pass
	
	def get_by_id(self, collection, _id):
		pass
	
	def update_by_id(self, collection, _id, value):
		pass
	
	def delete_by_id(self, collection, _id):
		pass
	
	def reset_db(self):
		pass

db_providers['dummy'] = DummyProvider
