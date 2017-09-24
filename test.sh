#!/bin/bash
coverage run --source=eos --omit='*/js.py','*/tests.py' -m unittest discover . -vvv || exit 1
coverage html
