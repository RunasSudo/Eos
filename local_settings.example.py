ORG_NAME = 'Your Organisation Here'

BASE_URI = 'http://localhost:5000'

SECRET_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxx'

AUTH_METHODS = [
	('email', 'Email'),
	('reddit', 'Reddit')
]

import eos.redditauth.election
ADMINS = [
	#eos.redditauth.election.RedditUser(username='xxxxxxxx')
]

TASK_RUN_STRATEGY = 'eos.core.tasks.direct.DirectRunStrategy'

TIMEZONE = 'Australia/Canberra'

# MongoDB

DB_TYPE = 'mongodb'
DB_URI = 'mongodb://localhost:27017/'
DB_NAME = 'eos'

# PostgreSQL

#DB_TYPE = 'postgresql'
#DB_URI = 'postgresql://'
#DB_NAME = 'eos'

# Email

MAIL_SERVER, MAIL_PORT = 'localhost', 25
MAIL_USERNAME, MAIL_PASSWORD = None, None
MAIL_DEFAULT_SENDER = 'eos@localhost'

# Reddit

REDDIT_OAUTH_CLIENT_ID = 'xxxxxxxxxxxxxx'
REDDIT_OAUTH_CLIENT_SECRET = 'xxxxxxxxxxxxxxxxxxxxxxxxxxx'
REDDIT_USER_AGENT = 'Application Title by /u/Your_Username'

# Security

CAST_IP = True
CAST_FINGERPRINT = False
