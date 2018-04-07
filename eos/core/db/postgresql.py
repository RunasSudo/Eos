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

import psycopg2
from psycopg2.sql import SQL, Identifier
import psycopg2.extras

import eos.core.db

class PostgreSQLDBProvider(eos.core.db.DBProvider):
	def connect(self):
		self.conn = psycopg2.connect(self.db_uri, dbname=self.db_name)
		self.cur = self.conn.cursor()
	
	def create_table(self, table):
		self.cur.execute(SQL('CREATE TABLE IF NOT EXISTS {} (_id uuid NOT NULL, data json, PRIMARY KEY (_id))').format(Identifier(table)))
		self.conn.commit()
	
	def get_all(self, table):
		self.create_table(table)
		self.cur.execute(SQL('SELECT data FROM {}').format(Identifier(table)))
		return [x[0] for x in self.cur.fetchall()]
	
	def get_all_by_fields(self, table, fields):
		# TODO: Make this much better
		result = []
		for val in self.get_all(table):
			if '_id' in fields and val['_id'] != fields.pop('_id'):
				continue
			if 'type' in fields and val['type'] != fields.pop('type'):
				continue
			for field in fields:
				if val['value'][field] != fields[field]:
					continue
			result.append(val)
		return result
	
	def get_by_id(self, table, _id):
		self.create_table(table)
		self.cur.execute(SQL('SELECT data FROM {} WHERE _id = %s').format(Identifier(table)), (_id,))
		return self.cur.fetchone()[0]
	
	def update_by_id(self, table, _id, value):
		self.create_table(table)
		self.cur.execute(SQL('INSERT INTO {} (_id, data) VALUES (%s, %s) ON CONFLICT (_id) DO UPDATE SET data = excluded.data').format(Identifier(table)), (_id, psycopg2.extras.Json(value)))
		self.conn.commit()
	
	def delete_by_id(self, table, _id):
		self.create_table(table)
		self.cur.execute(SQL('DELETE FROM {} WHERE _id = %s').format(Identifier(table)), (_id))
		self.conn.commit()
	
	def reset_db(self):
		self.cur.execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO postgres; GRANT ALL ON SCHEMA public TO public')
		self.conn.commit()

eos.core.db.db_providers['postgresql'] = PostgreSQLDBProvider
