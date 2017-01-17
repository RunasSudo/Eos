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

from django.conf.urls import url
import django.contrib.auth.views

from . import views

urlpatterns = [
	url(r'^(?P<election_id>[0-9a-f-]+)/view$$', views.election_view, name='election_view'),
	url(r'^(?P<election_id>[0-9a-f-]+)/questions$$', views.election_questions, name='election_questions'),
	url(r'^(?P<election_id>[0-9a-f-]+)/voting_booth$$', views.election_voting_booth, name='election_voting_booth'),
	url(r'^account/login', django.contrib.auth.views.login, {'authentication_form': views.LoginForm}, name='login'),
	url(r'^account/logout', django.contrib.auth.views.logout, name='logout'),
]
