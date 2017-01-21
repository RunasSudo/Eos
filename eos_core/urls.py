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
	url(r'^$', views.index, name='index'),
	url(r'^(?P<election_id>[0-9a-f-]+)$$', views.election_json, name='election_json'),
	url(r'^(?P<election_id>[0-9a-f-]+)/cast_vote$$', views.election_cast_vote, name='election_cast_vote'),
	url(r'^(?P<election_id>[0-9a-f-]+)/compute_result$$', views.election_compute_result, name='election_compute_result'),
]
