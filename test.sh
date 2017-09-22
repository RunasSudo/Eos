#!/bin/bash
ARGS=-vvv

for test in eos.core.tests eos.base.tests; do
	python -m unittest $test $ARGS || exit 1
done
