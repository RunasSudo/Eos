# Eos development notes

## Eos architecture overview

This Eos repository is split into a number of apps: `eos_core` and `eos_basic`.

`eos_core` contains the core Eos libraries, and some basic models and objects which every election should have. For example, each `Election` ought to have a title, times for the opening and closing of polls, etc., but the finer implementation details – most notably the form of the ballot, and the method of encrypting votes – is left to other apps: the former an implementation of `Question`; the latter a `Workflow`, composed of `WorkflowTask`s which we will discuss in greater detail later.

`eos_basic` implements basic (read: bad) implementations of these: an `ApprovalQuestion` for approval (or FPTP) elections, and various `WorkflowTasks` which implement a basic voting booth with *no* encryption (or ballot secrecy, or verifiability, etc).

Ideally, `eos_core` should contain no references to parts of `eos_basic`, and make no assumptions about implementation details. Of course, this means that the module is littered with them, and really should be cleaned up.

### EosObject

The centrepiece of Eos, which I will undoubtedly be crucified for, is `eos_core.libobjects`. The abstract class `EosObject` provides an interface for all Python objects which may be serialised to JSON in a deterministic manner, and used from both Python and Transcrypt. The goal is to allow a single implementation of the election and cryptographic primitives which may be shared by both the Django server side and the Javascript browser side. An `EosObject` must implement `serialise` and `_deserialise` methods (the latter with an underscore, because Transcrypt currently requires a wrapper function to deal with class methods).

Most `EosObject`s are of the `EosDictObject` variety, which serialises an object to a JSON dict based on the `eos_fields` field of the `EosMeta` subclass. See examples in `eos_*.objects` and `eos_*.models` for examples.

The `eos_js` module loads all definitions of `EosObject`s relevant for use in JavaScript, to be transpiled by Transcrypt. Thus it is important any modules loaded from this file avoid using libraries or functions not available to Transcrypt. For example, use `to_json`, `from_json`, `datetime`, `uuid`, etc. from the `eos_core.libobjects` module instead of the native Python versions, as these will be automatically mapped to the correct JavaScript equivalents.

#### Transcrypt notes

* `super()` is not supported
* `name` as an attribute is not supported
* `@classmethod` does not work correctly natively and requires a wrapper (until method decorators are implemented in Transcrypt)

### Workflows

The logic of conducting an election is contained in a `Workflow`, which contains a JSON list of `WorkflowTask`s. A basic workflow is:

```
[
	{"type": "eos_core.workflow.TaskSetElectionDetails", "value": null},
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
```
