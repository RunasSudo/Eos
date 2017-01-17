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

import eos_core.models

import django.shortcuts

# Authentication

import django.contrib.auth.forms
class LoginForm(django.contrib.auth.forms.AuthenticationForm):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['username'].widget.attrs['placeholder'] = 'Username'
		self.fields['password'].widget.attrs['placeholder'] = 'Password'

# Eos views

def election_view(request, election_id):
	election = django.shortcuts.get_object_or_404(eos_core.models.Election, id=election_id)
	return django.shortcuts.render(request, 'eos_basic/election_view.html', {'election': election})

def election_questions(request, election_id):
	election = django.shortcuts.get_object_or_404(eos_core.models.Election, id=election_id)
	return django.shortcuts.render(request, 'eos_basic/election_questions.html', {'election': election})

def election_voting_booth(request, election_id):
	election = django.shortcuts.get_object_or_404(eos_core.models.Election, id=election_id)
	return django.shortcuts.render(request, 'eos_basic/election_voting_booth.html', {'election': election})
