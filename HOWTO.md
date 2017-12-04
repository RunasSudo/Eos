# Deploying Eos

## General

Install the web dependencies.

    cd /path/to/Eos/eosweb/core
    bower install

Install the Python dependencies. (If doing this in a virtualenv, add the virtualenv path to *.gitignore*.)

    cd /path/to/Eos
    pip install -r requirements.txt

Build the JavaScript code.

    ./build_js.sh

## Standalone

Create *local_settings.py*.

    cd /path/to/Eos
    cp local_settings{.example,}.py

Modify *local_settings.py* as required.

Launch the server.

    cd /path/to/Eos
    FLASK_APP=eosweb EOSWEB_SETTINGS=$PWD/local_settings.py python -m flask run

Access Eos at http://localhost:5000/.

## Heroku

Add a MongoDB (recommended) or PostgreSQL resource to your Heroku app.

Set up the Heroku app.

    heroku git:remote -a your-app-12345

Create *local_settings.py*.

    cd /path/to/Eos
    cp local_settings{.example,}.py

Modify *local_settings.py* as required. Take special note of `BASE_URI` and the database information.

Set environment variables.

    heroku config:set EOSWEB_SETTINGS=/app/local_settings.py

Push the changes to the Heroku app.

    git add .
    git commit -m 'For Heroku'
    git push heroku master

Access Eos at https://your-app-12345.herokuapp.com/.

# Administering an election

There is not yet a GUI for administering an election – this must be done through the command line/Python interface.

## Creating an election

Firstly, access the Flask shell. Locally, run:

    FLASK_APP=eosweb EOSWEB_SETTINGS=$PWD/local_settings.py python -m flask shell

If on Heroku, run:

    heroku run FLASK_APP=eosweb python -m flask shell

Then create the election using the Python API. For example:

```python
from eos.core.objects import *
from eos.base.election import *
from eos.psr.crypto import *
from eos.psr.election import *
from eos.psr.workflow import *

election = PSRElection()
election.workflow = PSRWorkflow()

# Set election details
election.name = 'Test Election'
#election.kind = 'referendum' # Uncomment this line to change the kind of vote being held

from eos.redditauth.election import RedditUser
election.voters.append(UserVoter(user=EmailUser(name='Alice', email='alice@localhost')))
election.voters.append(UserVoter(user=EmailUser(name='Bob', email='bob@localhost')))
election.voters.append(UserVoter(user=EmailUser(name='Carol', email='carol@localhost')))
election.voters.append(UserVoter(user=RedditUser(username='RunasSudo')))

# At least two mixing trustees are required to preserve ballot secrecy
election.mixing_trustees.append(InternalMixingTrustee(name='Eos Voting'))
election.mixing_trustees.append(InternalMixingTrustee(name='Eos Voting'))

election.sk = EGPrivateKey.generate()
election.public_key = election.sk.public_key

election.questions.append(ApprovalQuestion(prompt='Pineapple on pizza?', choices=['Yes', 'No'], min_choices=0, max_choices=1))

# Freeze election
election.workflow.get_task('eos.base.workflow.TaskConfigureElection').enter()

# Open voting
election.workflow.get_task('eos.base.workflow.TaskOpenVoting').enter()

election.save()
```

If you are using the email log in method (`EmailUser`), you can additionally email the log in details using, for example:

```python
for voter in election.voters:
    if isinstance(voter, UserVoter):
        if isinstance(voter.user, EmailUser):
            voter.user.email_password(app.config['SMTP_HOST'], app.config['SMTP_PORT'], app.config['SMTP_USER'], app.config['SMTP_PASS'], app.config['SMTP_FROM'])
```

You should now be able to see the election in the web interface.

Exit the Flask shell by pressing Ctrl+D.

## Closing and counting an election

To close an election, helper commands are available, so use of the Flask shell is not required. Locally, run:

    FLASK_APP=eosweb EOSWEB_SETTINGS=$PWD/local_settings.py python -m flask close_election

On Heroku, run:

    heroku run FLASK_APP=eosweb python -m flask close_election

This will close the first election found. If there are multiple elections, you can select which one to close by passing the `--electionid` flag, for example:

    FLASK_APP=eosweb EOSWEB_SETTINGS=$PWD/local_settings.py python -m flask close_election --electionid 01234567-89ab-cdef-ghij-klmnopqrstuv

Repeat this process, but substitute `count_election` for `close_election` to count the ballots and release the results.

You should now be able to see the results in the web interface.
