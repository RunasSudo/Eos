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

from django.conf.urls import include, url

from . import views

urlpatterns = [
	url(r'^(?P<election_id>[0-9a-f-]+)/trustees$$', views.election_trustees, name='election_trustees'),
	url(r'^trustee/(?P<trustee_id>[0-9a-f-]+)/$$', views.trustee_home, name='trustee_home'),
]
