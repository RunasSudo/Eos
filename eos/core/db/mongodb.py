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

import eos.core.db

class MongoDBProvider(eos.core.db.DBProvider):
	def connect(self):
		self.client = pymongo.MongoClient(self.db_uri)
		self.db = self.client[self.db_name]
	
	def get_all(self, collection):
		return self.db[collection].find()
	
	def get_by_id(self, collection, _id):
		return self.db[collection].find_one(_id)
	
	def update_by_id(self, collection, _id, value):
		self.db[collection].replace_one({'_id': _id}, value, upsert=True)
	
	def reset_db(self):
		self.client.drop_database(self.db_name)

eos.core.db.db_providers['mongodb'] = MongoDBProvider
