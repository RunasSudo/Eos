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
import eos_core.libobjects
import eos_core.workflow

import eos_basic.objects # TODO: UH OH!

import django.core.exceptions
import django.http
import django.shortcuts
import django.utils.timezone

def index(request):
	return django.shortcuts.render(request, 'eos_core/index.html', {'workflow_tasks': eos_core.workflow.WorkflowTask.get_all() })

def election_json(request, election_id):
	election = django.shortcuts.get_object_or_404(eos_core.models.Election, id=election_id)
	return django.http.HttpResponse(eos_core.libobjects.to_json(eos_core.libobjects.EosObject.serialise_and_wrap(election, None, request.GET.get('hashed', 'false') == 'true')), content_type='application/json')

def election_cast_vote(request, election_id):
	election = django.shortcuts.get_object_or_404(eos_core.models.Election, id=election_id)
	
	if election.voting_has_closed or not election.voting_has_opened:
		raise django.core.exceptions.PermissionDenied('Voting in this election is not yet open or has closed')
	
	encrypted_vote = eos_core.libobjects.EosObject.deserialise_and_unwrap(eos_core.libobjects.from_json(request.POST['encrypted_vote']), None)
	
	voter = eos_basic.objects.DjangoAuthVoter(request.user.id)
	
	cast_vote = eos_core.models.CastVote(
		election=election,
		voter=voter,
		encrypted_vote=encrypted_vote,
		vote_received_at=django.utils.timezone.now(),
	)
	cast_vote.save()
	
	return django.http.HttpResponse(status=204)

def election_compute_result(request, election_id):
	pass
