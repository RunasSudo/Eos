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

import click
import flask

from eos.base.election import *
from eos.psr.crypto import *
from eos.psr.election import *
from eos.psr.mixnet import *
from eos.psr.workflow import *

import eos.core.hashing
import eosweb

import functools

app = flask.Flask(__name__)

@app.cli.command('test')
@click.option('--prefix', default=None)
@click.option('--lang', default=None)
def run_tests(prefix, lang):
	import eos.tests
	eos.tests.run_tests(prefix, lang)

# TODO: Will remove this once we have a web UI
@app.cli.command('drop_db_and_setup')
def setup_test_election():
	# DANGER!
	client.drop_database('test')
	
	# Set up election
	election = PSRElection()
	election.workflow = PSRWorkflow()
	
	# Set election details
	election.name = 'Test Election'
	
	voter = Voter()
	election.voters.append(Voter(name='Alice'))
	election.voters.append(Voter(name='Bob'))
	election.voters.append(Voter(name='Charlie'))
	
	election.mixing_trustees.append(MixingTrustee(name='Eos Voting'))
	
	election.sk = EGPrivateKey.generate()
	election.public_key = election.sk.public_key
	
	question = ApprovalQuestion(prompt='President', choices=['John Smith', 'Joe Bloggs', 'John Q. Public'], min_choices=0, max_choices=2)
	election.questions.append(question)
	
	question = ApprovalQuestion(prompt='Chairman', choices=['John Doe', 'Andrew Citizen'], min_choices=0, max_choices=1)
	election.questions.append(question)
	
	election.save()
	
	# Freeze election
	election.workflow.get_task('eos.base.workflow.TaskConfigureElection').enter()
	
	# Open voting
	election.workflow.get_task('eos.base.workflow.TaskOpenVoting').enter()
	
	election.save()

@app.context_processor
def inject_globals():
	return {'eos': eos, 'eosweb': eosweb, 'SHA256': eos.core.hashing.SHA256}

@app.route('/')
def index():
	return flask.render_template('index.html')

def using_election(func):
	@functools.wraps(func)
	def wrapped(election_id):
		election = Election.get_by_id(election_id)
		return func(election)
	return wrapped

@app.route('/election/<election_id>/')
@using_election
def election_api_json(election):
	return flask.Response(EosObject.to_json(EosObject.serialise_and_wrap(election, should_protect=True)), mimetype='application/json')

@app.route('/election/<election_id>/view')
@using_election
def election_view(election):
	return flask.render_template('election/view.html', election=election)

@app.route('/election/<election_id>/booth')
@using_election
def election_booth(election):
	selection_model_view_map = EosObject.to_json({key._name: val for key, val in model_view_map.items()}) # ewww
	
	return flask.render_template('election/booth.html', election=election, selection_model_view_map=selection_model_view_map)

@app.route('/election/<election_id>/view/questions')
@using_election
def election_view_questions(election):
	return flask.render_template('election/questions.html', election=election)

@app.route('/election/<election_id>/view/ballots')
@using_election
def election_view_ballots(election):
	return flask.render_template('election/ballots.html', election=election)

@app.route('/election/<election_id>/view/trustees')
@using_election
def election_view_trustees(election):
	return flask.render_template('election/trustees.html', election=election)



# === Model-Views ===

model_view_map = {}

# TODO: Make more modular
from . import modelview
model_view_map.update(modelview.model_view_map)
