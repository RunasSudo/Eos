#!/bin/bash
#   Eos - Verifiable elections
#   Copyright © 2017  RunasSudo (Yingtong Li)
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

set +e

FLAGS=-k

for f in eos.js eos.js_tests; do
	transcrypt -b -n $FLAGS $f.py
	
	# Javascript identifiers cannot contain dots
	perl -0777 -pi -e 's/eos.js/eosjs/g' eos/__javascript__/$f.js
	
	# __pragma__ sometimes stops working???
	perl -0777 -pi -e "s/__pragma__ \('.*?'\)//gs" eos/__javascript__/$f.js
	
	# Transcrypt by default suppresses stack traces for some reason??
	perl -0777 -pi -e "s/__except0__.__cause__ = null;//g" eos/__javascript__/$f.js
done
