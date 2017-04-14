#!/bin/bash
sudo systemctl restart postgresql
dropdb eos
createdb eos
./manage.py migrate
cat <<EOF | ./manage.py shell
# Create superuser
from django.contrib.auth.models import User
User.objects.create_superuser("admin", "admin@localhost", "eosadmin123")
# Initialise basic workflow
import eos_core.models
import eos_core.libobjects
workflow = eos_core.models.Workflow(workflow_name='Basic Workflow', tasks=eos_core.libobjects.EosObject.deserialise_list(eos_core.libobjects.from_json("""
[
	{"type": "eos_sgjjr.workflow.TaskSetElectionDetailsAndTrustees", "value": null},
	{"type": "eos_core.workflow.TaskOpenVoting", "value": null},
	{"type": "eos_basic.workflow.TaskReceiveVotes", "value": {
		"booth_tasks": [
			{"type": "eos_basic.workflow.BoothTaskWelcome", "value": null},
			{"type": "eos_basic.workflow.BoothTaskMakeSelections", "value": null},
			{"type": "eos_basic.workflow.BoothTaskReviewSelections", "value": null},
			{"type": "eos_basic.workflow.BoothTaskEncryptBallot", "value": null},
			{"type": "eos_basic.workflow.BoothTaskAuditBallot", "value": null},
			{"type": "eos_basic.workflow.BoothTaskCastVote", "value": null}
		]
	}},
	{"type": "eos_core.workflow.TaskExtendVoting", "value": null},
	{"type": "eos_core.workflow.TaskCloseVoting", "value": null},
	{"type": "eos_basic.workflow.TaskComputeResult", "value": null},
	{"type": "eos_core.workflow.TaskReleaseResult", "value": null}
]
"""), None))
workflow.save()
# Create new election
user1 = User.objects.create_user('trustee1', 'trustee1@localhost', 'eosadmin123')
user2 = User.objects.create_user('trustee2', 'trustee2@localhost', 'eosadmin123')
import eos_sgjjr.models
election = eos_sgjjr.models.ElectionWithTrustees(
	election_name='Election 1',
	workflow=workflow,
	questions=eos_core.libobjects.EosObject.deserialise_list(eos_core.libobjects.from_json("""[{"type": "eos_basic.objects.ApprovalQuestion", "value": {"choices": ["John Smith", "Joe Bloggs", "John Q Public"], "description": "Vote now", "max_choices": 1, "min_choices": 0, "title": "President"}}]"""), None),
	voter_eligibility=eos_core.libobjects.EosObject.deserialise_and_unwrap(eos_core.libobjects.from_json("""{"type": "eos_basic.objects.UnconditionalVoterEligibility", "value": null}"""), None)
)
election.save()
eos_sgjjr.models.SGJJRTrustee(election=election, order=1, auth_user_id=user1.id).save()
eos_sgjjr.models.SGJJRTrustee(election=election, order=2, auth_user_id=user2.id).save()
EOF
