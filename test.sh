#!/bin/bash
coverage run --source=eos --omit='*/js.py','eos/js_tests.py' -m eos.tests $* || exit 1
coverage html
