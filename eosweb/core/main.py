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
import timeago

from eos.core.objects import *
from eos.core.tasks import *
from eos.base.election import *
from eos.base.tasks import *
from eos.base.workflow import *
from eos.psr.crypto import *
from eos.psr.election import *
from eos.psr.mixnet import *
from eos.psr.workflow import *

import eos.core.hashing
import eosweb

from datetime import datetime

import functools
import importlib
import io
import json
import os
import pytz
import subprocess

app = flask.Flask(__name__, static_folder=None)

# Load config
app.config.from_object('eosweb.core.settings')
if 'EOSWEB_SETTINGS' in os.environ:
	app.config.from_envvar('EOSWEB_SETTINGS')

# Load app config
for app_name in app.config['APPS']:
	app.config.from_object(app_name + '.settings')
if 'EOSWEB_SETTINGS' in os.environ:
	app.config.from_envvar('EOSWEB_SETTINGS')

# Connect to database
db_connect(app.config['DB_NAME'], app.config['DB_URI'], app.config['DB_TYPE'])

# Set configs
User.admins = app.config['ADMINS']

# Make Flask's serialisation, e.g. for sessions, EosObject aware
class EosObjectJSONEncoder(flask.json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, EosObject):
			return EosObject.serialise_and_wrap(obj)
		return super().default(obj)
class EosObjectJSONDecoder(flask.json.JSONDecoder):
	def __init__(self, *args, **kwargs):
		self.super_object_hook = kwargs.get('object_hook', None)
		kwargs['object_hook'] = self.my_object_hook
		super().__init__(*args, **kwargs)
	
	def my_object_hook(self, val):
		if 'type' in val:
			if val['type'] in EosObject.objects:
				return EosObject.deserialise_and_unwrap(val)
		if self.super_object_hook:
			return self.super_object_hook(val)
		return val
app.json_encoder = EosObjectJSONEncoder
app.json_decoder = EosObjectJSONDecoder

# Patch Flask's static file sending to add no-cache
# Allow "caching", but require revalidation via 304 Not Modified
@app.route('/static/<path:filename>')
def static(filename):
	cache_timeout = app.get_send_file_max_age(filename)
	val = flask.send_from_directory('static', filename, cache_timeout=cache_timeout)
	val.headers['Cache-Control'] = val.headers['Cache-Control'].replace('public', 'no-cache')
	#import pdb; pdb.set_trace()
	return val

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
	dbinfo.provider.reset_db()
	
	# Set up election
	election = PSRElection()
	election.workflow = PSRWorkflow()
	
	# Set election details
	election.name = 'Test Election'
	
	from eos.redditauth.election import RedditUser
	election.voters.append(UserVoter(user=EmailUser(name='Alice', email='alice@localhost')))
	election.voters.append(UserVoter(user=EmailUser(name='Bob', email='bob@localhost')))
	election.voters.append(UserVoter(user=EmailUser(name='Carol', email='carol@localhost')))
	election.voters.append(UserVoter(user=RedditUser(username='RunasSudo')))
	
	for voter in election.voters:
		if isinstance(voter, UserVoter):
			if isinstance(voter.user, EmailUser):
				voter.user.email_password(app.config['SMTP_HOST'], app.config['SMTP_PORT'], app.config['SMTP_USER'], app.config['SMTP_PASS'], app.config['SMTP_FROM'])
	
	election.mixing_trustees.append(InternalMixingTrustee(name='Eos Voting'))
	election.mixing_trustees.append(InternalMixingTrustee(name='Eos Voting'))
	
	election.sk = EGPrivateKey.generate()
	election.public_key = election.sk.public_key
	
	question = PreferentialQuestion(prompt='President', choices=[
		Ticket(name='ACME Party', choices=[
			Choice(name='John Smith'),
			Choice(name='Joe Bloggs', party='Independent ACME')
		]),
		Choice(name='John Q. Public')
	], min_choices=0, max_choices=3, randomise_choices=True)
	election.questions.append(question)
	
	question = ApprovalQuestion(prompt='Chairman', choices=[Choice(name='John Doe'), Choice(name='Andrew Citizen')], min_choices=0, max_choices=1)
	election.questions.append(question)
	
	election.save()

@app.cli.command('verify_election')
@click.option('--electionid', default=None)
def verify_election(electionid):
	if electionid is None:
		election = Election.get_all()[0]
	else:
		election = Election.get_by_id(electionid)
	
	election.verify()
	print('The election has passed validation')

@app.cli.command('tally_stv')
@click.option('--electionid', default=None)
@click.option('--qnum', default=0)
@click.option('--randfile', default=None)
def tally_stv_election(electionid, qnum, randfile):
	election = Election.get_by_id(electionid)
	
	with open(randfile, 'r') as f:
		dat = json.load(f)
	task = TaskTallySTV(
		election_id=election._id,
		q_num=qnum,
		random=dat,
		num_seats=7,
		status=Task.Status.READY,
		run_strategy=EosObject.lookup(app.config['TASK_RUN_STRATEGY'])()
	)
	task.save()
	task.run()

@app.context_processor
def inject_globals():
	return {'eos': eos, 'eosweb': eosweb, 'SHA256': eos.core.hashing.SHA256}

@app.template_filter('pretty_date')
def pretty_date(dt):
	dt_local = dt.astimezone(pytz.timezone(app.config['TIMEZONE']))
	return flask.Markup('<time datetime="{}" title="{}">{}</time>'.format(dt_local.strftime('%Y-%m-%dT%H:%M:%S%z'), dt_local.strftime('%Y-%m-%d %H:%M:%S %Z'), timeago.format(dt, DateTimeField.now())))

# Tickle the plumbus every request
@app.before_request
def tick_scheduler():
	# Process pending tasks
	TaskScheduler.tick()

# === Views ===

@app.route('/')
def index():
	return flask.render_template('index.html')

def using_election(func):
	@functools.wraps(func)
	def wrapped(election_id, **kwargs):
		election = Election.get_by_id(election_id)
		return func(election, **kwargs)
	return wrapped

def election_admin(func):
	@functools.wraps(func)
	def wrapped(election, **kwargs):
		if 'user' in flask.session and flask.session['user'].is_admin():
			return func(election, **kwargs)
		else:
			return flask.Response('Administrator credentials required', 403)
	return wrapped

@app.route('/election/<election_id>/')
@using_election
def election_api_json(election):
	is_full = 'full' in flask.request.args
	return flask.Response(EosObject.to_json(EosObject.serialise_and_wrap(election, None, SerialiseOptions(should_protect=True, for_hash=(not is_full), combine_related=True))), mimetype='application/json')

@app.route('/election/<election_id>/view')
@using_election
def election_view(election):
	return flask.render_template('election/view/view.html', election=election)

@app.route('/election/<election_id>/booth')
@using_election
def election_booth(election):
	selection_model_view_map = EosObject.to_json({key._name: val for key, val in model_view_map.items()}) # ewww
	auth_methods = EosObject.to_json(app.config['AUTH_METHODS'])
	
	return flask.render_template('election/view/booth.html', election=election, selection_model_view_map=selection_model_view_map, auth_methods=auth_methods)

@app.route('/election/<election_id>/view/questions')
@using_election
def election_view_questions(election):
	return flask.render_template('election/view/questions.html', election=election)

@app.route('/election/<election_id>/view/ballots')
@using_election
def election_view_ballots(election):
	return flask.render_template('election/view/ballots.html', election=election)

@app.route('/election/<election_id>/view/trustees')
@using_election
def election_view_trustees(election):
	return flask.render_template('election/view/trustees.html', election=election)

@app.route('/election/<election_id>/admin')
@using_election
@election_admin
def election_admin_summary(election):
	return flask.render_template('election/admin/admin.html', election=election)

@app.route('/election/<election_id>/admin/enter_task')
@using_election
@election_admin
def election_admin_enter_task(election):
	workflow_task = election.workflow.get_task(flask.request.args['task_name'])
	if workflow_task.status != WorkflowTask.Status.READY:
		return flask.Response('Task is not yet ready or has already exited', 409)
	
	task = WorkflowTaskEntryTask(
		election_id=election._id,
		workflow_task=workflow_task._name,
		status=Task.Status.READY,
		run_strategy=EosObject.lookup(app.config['TASK_RUN_STRATEGY'])()
	)
	task.run()
	
	return flask.redirect(flask.url_for('election_admin_summary', election_id=election._id))

@app.route('/election/<election_id>/admin/schedule_task', methods=['POST'])
@using_election
@election_admin
def election_admin_schedule_task(election):
	workflow_task = election.workflow.get_task(flask.request.form['task_name'])
	
	task = WorkflowTaskEntryTask(
		election_id=election._id,
		workflow_task=workflow_task._name,
		run_at=DateTimeField().deserialise(flask.request.form['datetime']),
		status=Task.Status.READY,
		run_strategy=EosObject.lookup(app.config['TASK_RUN_STRATEGY'])()
	)
	task.save()
	
	return flask.redirect(flask.url_for('election_admin_summary', election_id=election._id))

@app.route('/election/<election_id>/cast_ballot', methods=['POST'])
@using_election
def election_api_cast_vote(election):
	if election.workflow.get_task('eos.base.workflow.TaskOpenVoting').status < WorkflowTask.Status.EXITED or election.workflow.get_task('eos.base.workflow.TaskCloseVoting').status > WorkflowTask.Status.READY:
		# Voting is not yet open or has closed
		return flask.Response('Voting is not yet open or has closed', 409)
	
	data = json.loads(flask.request.data)
	
	if 'user' not in flask.session:
		# User is not authenticated
		return flask.Response('Not authenticated', 403)
	
	voter = None
	for election_voter in election.voters:
		if election_voter.user.matched_by(flask.session['user']):
			voter = election_voter
			break
	
	if voter is None:
		# Invalid user
		return flask.Response('Invalid credentials', 403)
	
	# Cast the vote
	ballot = EosObject.deserialise_and_unwrap(data['ballot'])
	vote = Vote(voter_id=voter._id, ballot=ballot, cast_at=DateTimeField.now())
	
	# Store data
	if app.config['CAST_FINGERPRINT']:
		vote.cast_fingerprint = data['fingerprint']
	if app.config['CAST_IP']:
		if os.path.exists('/app/.heroku'):
			vote.cast_ip = flask.request.headers['X-Forwarded-For'].split(',')[-1]
		else:
			vote.cast_ip = flask.request.remote_addr
	
	vote.save()
	
	return flask.Response(json.dumps({
		'voter': EosObject.serialise_and_wrap(voter, None, SerialiseOptions(should_protect=True)),
		'vote': EosObject.serialise_and_wrap(vote, None, SerialiseOptions(should_protect=True))
	}), mimetype='application/json')

@app.route('/election/<election_id>/export/question/<int:q_num>/<format>')
@using_election
def election_api_export_question(election, q_num, format):
	import eos.base.util.blt
	resp = flask.send_file(io.BytesIO('\n'.join(eos.base.util.blt.writeBLT(election, q_num, 2)).encode('utf-8')), mimetype='text/plain; charset=utf-8', attachment_filename='{}.blt'.format(q_num), as_attachment=True)
	resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
	return resp

@app.route('/auditor')
def auditor():
	return flask.render_template('election/auditor.html')

@app.route('/debug')
def debug():
	assert False

@app.route('/auth/login')
def login():
	return flask.render_template('auth/login.html')

@app.route('/auth/logout')
def logout():
	flask.session['user'] = None
	#return flask.redirect(flask.request.args['next'] if 'next' in flask.request.args else '/')
	# I feel like there's some kind of exploit here, so we'll leave this for now
	return flask.redirect('/')

@app.route('/auth/login_complete')
def login_complete():
	return flask.render_template('auth/login_complete.html')

@app.route('/auth/login_cancelled')
def login_cancelled():
	return flask.render_template('auth/login_cancelled.html')

@app.route('/auth/email/login')
def email_login():
	return flask.render_template('auth/email/login.html')

@app.route('/auth/email/authenticate', methods=['POST'])
def email_authenticate():
	user = None
	
	for election in Election.get_all():
		for voter in election.voters:
			if isinstance(voter.user, EmailUser):
				if voter.user.email.lower() == flask.request.form['email'].lower():
					if voter.user.password == flask.request.form['password']:
						user = voter.user
						break
	
	if user is None:
		return flask.render_template('auth/email/login.html', error='The email or password you entered was invalid. Please check your details and try again. If the issue persists, contact the election administrator.')
	
	flask.session['user'] = user
	
	return flask.redirect(flask.url_for('login_complete'))

@app.route('/email')
def tmp():
	import sass
	css = sass.compile(string=flask.render_template('email/base.scss'))
	return flask.render_template('email/base.html', title='Hello World', text='<p>Dear voter,</p><p>You are registered to vote in the election Election Name.</p>', css=css)

# === Apps ===

for app_name in app.config['APPS']:
	app_main = importlib.import_module(app_name + '.main')
	app_main.main(app)

# === Model-Views ===

model_view_map = {}

# TODO: Make more modular
from . import modelview
model_view_map.update(modelview.model_view_map)
