ORG_NAME = 'Your Organisation Here'

SECRET_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxx'

AUTH_METHODS = [
	('email', 'Email'),
	('reddit', 'Reddit')
]

# MongoDB

DB_TYPE = 'mongodb'
DB_URI = 'mongodb://localhost:27017/'
DB_NAME = 'eos'

# Email

SMTP_HOST, SMTP_PORT = 'localhost', 25
SMTP_USER, SMTP_PASS = None, None
SMTP_FROM = 'eos@localhost'

# Reddit

REDDIT_OAUTH_CLIENT_ID = 'xxxxxxxxxxxxxx'
REDDIT_OAUTH_CLIENT_SECRET = 'xxxxxxxxxxxxxxxxxxxxxxxxxxx'
REDDIT_USER_AGENT = 'Application Title by /u/Your_Username'
