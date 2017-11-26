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

ORG_NAME = 'FIXME'

BASE_URI = 'http://localhost:5000'

MONGO_URI = 'mongodb://localhost:27017/'
DB_NAME = 'eos'

SECRET_KEY = 'FIXME'

APPS = [
	'eosweb.redditauth'
]

AUTH_METHODS = [
	('email', 'Email')
]

SMTP_HOST, SMTP_PORT = 'localhost', 25
SMTP_USER, SMTP_PASS = None, None
SMTP_FROM = 'eos@localhost'
