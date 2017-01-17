#!/bin/bash
#    Copyright © 2017  RunasSudo (Yingtong Li)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

transcrypt -bnakv eos_js.py
cp __javascript__/eos_js.js eos_basic/static/eos_basic/js/build/eos_js.js

# Patch the files
# Javascript identifiers cannot contain dots
#perl -pi -e 's/eos_core.objects \(\)/eos_core_objects ()/g' eos_basic/static/eos_basic/js/build/eos_core.objects.js
# Transcrypt attempts to initialise circularly-imported modules before they are ready
#perl -pi -e 's/\(!module.__inited__\)/(!module.__inited__ \&\& module.__all__)/g' eos_basic/static/eos_basic/js/build/eos_core.objects.js
# __pragma__ sometimes stops working???
perl -0777 -pi -e "s/__pragma__ \('.*?'\)//gs" eos_basic/static/eos_basic/js/build/eos_js.js
