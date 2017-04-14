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
import eos_core.views
import eos_sgjjr.models

import django.shortcuts

def election_trustees(request, election_id):
	election = eos_core.views.get_subclass_or_404(eos_core.models.Election, id=election_id)
	return django.shortcuts.render(request, 'eos_sgjjr/election_trustees.html', {'election': election})

def trustee_home(request, trustee_id):
	trustee = eos_core.views.get_subclass_or_404(eos_sgjjr.models.Trustee, id=trustee_id)
	return django.shortcuts.render(request, 'eos_sgjjr/trustee_home.html', {'trustee': trustee, 'election': trustee.election})
