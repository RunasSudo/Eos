#   Eos - Verifiable elections
#   Copyright © 2017-2019  RunasSudo (Yingtong Li)
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

import flask

from eos.nsauth.election import *

import urllib.request, urllib.parse

blueprint = flask.Blueprint('eosweb.nsauth', __name__, template_folder='templates')

app = None

@blueprint.record
def reddit_register(setup_state):
	global app
	app = setup_state.app

@blueprint.route('/auth/nationstates/login')
def nationstates_login():
	return flask.render_template('auth/nationstates/login.html')

@blueprint.route('/auth/nationstates/authenticate', methods=['POST'])
def nationstates_authenticate():
	username = flask.request.form['username'].lower().strip().replace(' ', '_')
	
	with urllib.request.urlopen(urllib.request.Request('https://www.nationstates.net/cgi-bin/api.cgi?a=verify&' + urllib.parse.urlencode({'nation': username, 'checksum': flask.request.form['checksum']}), headers={'User-Agent': app.config['NATIONSTATES_USER_AGENT']})) as resp:
		if resp.read().decode('utf-8').strip() != '1':
			return flask.render_template('auth/nationstates/login.html', error='The nation name or verification code you entered was invalid. Please check your details and try again. If the issue persists, contact the election administrator.')
	
	flask.session['user'] = NationStatesUser(username=username)
	
	return flask.redirect(flask.url_for('login_complete'))
