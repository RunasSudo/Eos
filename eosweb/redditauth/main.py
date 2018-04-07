#   Eos - Verifiable elections
#   Copyright © 2017-18  RunasSudo (Yingtong Li)
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

from flask_oauthlib.client import OAuth

import flask

from eos.redditauth.election import *

import base64
import uuid

blueprint = flask.Blueprint('eosweb.redditauth', __name__)

app = None
oauth = None
reddit = None

@blueprint.record
def reddit_register(setup_state):
	global app, oauth, reddit
	
	app = setup_state.app
	
	oauth = OAuth()
	reddit = oauth.remote_app('Reddit',
		request_token_url=None,
		authorize_url='https://www.reddit.com/api/v1/authorize.compact',
		request_token_params={'duration': 'temporary', 'scope': 'identity'},
		access_token_url='https://www.reddit.com/api/v1/access_token',
		access_token_method='POST',
		access_token_headers={
			'Authorization': 'Basic ' + base64.b64encode('{}:{}'.format(app.config['REDDIT_OAUTH_CLIENT_ID'], app.config['REDDIT_OAUTH_CLIENT_SECRET']).encode('ascii')).decode('ascii'),
			'User-Agent': app.config['REDDIT_USER_AGENT']
		},
		consumer_key=app.config['REDDIT_OAUTH_CLIENT_ID'],
		consumer_secret=app.config['REDDIT_OAUTH_CLIENT_SECRET']
	)
	
	@reddit.tokengetter
	def get_reddit_oauth_token():
		return (flask.session.get('user').oauth_token, '')

@blueprint.route('/auth/reddit/login')
def reddit_login():
	return reddit.authorize(callback=app.config['BASE_URI'] + flask.url_for('eosweb.redditauth.reddit_oauth_authorized'), state=uuid.uuid4())

@blueprint.route('/auth/reddit/oauth_callback')
def reddit_oauth_authorized():
	resp = reddit.authorized_response()
	if resp is None:
		# Request denied
		return flask.redirect(flask.url_for('login_cancelled'))
	
	user = RedditUser()
	user.oauth_token = resp['access_token']
	flask.session['user'] = user
	
	me = reddit.get('https://oauth.reddit.com/api/v1/me', headers={
		'User-Agent': app.config['REDDIT_USER_AGENT']
	})
	user.username = me.data['name']
	
	return flask.redirect(flask.url_for('login_complete'))
