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

import django.contrib.staticfiles.storage
import django.core.urlresolvers
import django.utils.timezone
import jinja2

def jinja2_url(name, *args):
	return django.core.urlresolvers.reverse(name, args=args)

def jinja2_datetime(dt):
	return django.utils.timezone.template_localtime(dt).strftime('%Y-%m-%d %H:%M')

def environment(**options):
	env = jinja2.Environment(**options)
	env.globals.update({
		'static': django.contrib.staticfiles.storage.staticfiles_storage.url,
		'url': jinja2_url,
	})
	env.filters.update({
		'datetime': jinja2_datetime,
	})
	return env
