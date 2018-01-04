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

from eos.core.tasks import *
from eos.base.election import *

class WebTask(Task):
	def error(self):
		import eosweb
		
		# Prepare email
		title = 'Task failed: {}'.format(self.label)
		
		css = sass.compile(string=flask.render_template('email/base.scss'))
		html = flask.render_template(
			'email/base.html',
			title=title,
			css=css,
			text='<p>The task <i>{}</i> failed execution. The output was:</p><pre>{}</pre>'.format(self.label, '\n'.join(self.messages))
		)
		html = premailer.Premailer(html).transform()
		
		body = flask.render_template(
			'email/base.txt',
			title=title,
			text='The task "{}" failed execution. The output was:\n\n{}'.format(self.label, '\n'.join(self.messages))
		)
		
		# Send email
		mail = flask_mail.Mail(eosweb.app)
		msg = flask_mail.Message(
			title,
			recipients=[admin.email for admin in eosweb.app.config['ADMINS'] if isinstance(admin, EmailUser)],
			body=body,
			html=html
		)
		mail.send(msg)

class WorkflowTaskEntryWebTask(WorkflowTaskEntryTask, WebTask):
	pass
