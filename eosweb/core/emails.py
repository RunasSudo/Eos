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

import logging
import premailer
import sass

import flask
import flask_mail

from eos.base.election import *

def send_email(title, html_text, body_text, recipients):
	# Prepare email
	css = sass.compile(string=flask.render_template('email/base.scss'))
	html = flask.render_template(
		'email/base.html',
		title=title,
		css=css,
		text=html_text
	)
	html = premailer.Premailer(html, strip_important=False).transform()
	
	body = flask.render_template(
		'email/base.txt',
		title=title,
		text=body_text
	)
	
	# Send email
	mail = flask_mail.Mail(flask.current_app)
	msg = flask_mail.Message(
		title,
		recipients=recipients,
		body=body,
		html=html
	)
	mail.send(msg)

def voter_email_password(election, voter):
	send_email(
		'Registered to vote: {}'.format(election.name),
		'<p>Dear {},</p><p>You are registered to vote in <i>{}</i>.</p><p>Your login details are as follows:</p><p>Email: <code>{}</code></p><p>Password: <code>{}</code></p>'.format(voter.name, election.name, voter.user.email, voter.user.password),
		'Dear {},\n\nYou are registered to vote in "{}".\n\nYour login details are as follows:\n\nEmail: {}\nPassword: {}'.format(voter.name, election.name, voter.user.email, voter.user.password),
		[voter.user.email]
	)

def task_email_failure(task):
	send_email(
		'Task failed: {}'.format(task.label),
		'<p>The task <i>{}</i> failed execution. The output was:</p><pre>{}</pre>'.format(task.label, '\n'.join(task.messages)),
		'The task "{}" failed execution. The output was:\n\n{}'.format(task.label, '\n'.join(task.messages)),
		[admin.email for admin in flask.current_app.config['ADMINS'] if isinstance(admin, EmailUser)]
	)
