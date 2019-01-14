#!/bin/bash
#   Eos - Verifiable elections
#   Copyright © 2017-2019  RunasSudo (Yingtong Li)
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

FLAGS="-k -mc -o"

#for f in eos.js eos.js_tests; do
for f in eos.js_tests; do
	transcrypt -b -n $FLAGS $f.py || exit 1
done

# Transcrypt syntax errors
perl -0777 -pi -e 's/import \{, /import \{/g' __target__/eos*.js

# Add export
echo >> __target__/eos.js_tests.js
echo 'export {eos, __kwargtrans__};' >> __target__/eos.js_tests.js

# Convert to ES5
./node_modules/.bin/browserify -t babelify -r ./__target__/eos.js_tests.js:eosjs > eosweb/core/static/js/eosjs.js
