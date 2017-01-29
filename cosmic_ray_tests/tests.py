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

import unittest

import os

class CryptoTest(unittest.TestCase):
	def test_django(self):
		os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eos.settings")
		from django.core.management import execute_from_command_line
		execute_from_command_line(["./manage.py", "test", "--verbosity", "3", "--failfast", "--noinput", "--keepdb", "eos_stjjr"])
