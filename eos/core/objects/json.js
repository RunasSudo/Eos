/*
	Copyright © 2017 RunasSudo (Yingtong Li)
	Based on json-stable-stringify by substack, licensed under the MIT License.
	
	Permission is hereby granted, free of charge, to any person obtaining a copy
	of this software and associated documentation files (the "Software"), to deal
	in the Software without restriction, including without limitation the rights
	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
	copies of the Software, and to permit persons to whom the Software is
	furnished to do so, subject to the following conditions:
	
	The above copyright notice and this permission notice shall be included in all
	copies or substantial portions of the Software.
	
	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
	SOFTWARE.
*/

var isArray = Array.isArray || function (x) {
	return {}.toString.call(x) === '[object Array]';
};

var objectKeys = Object.keys || function (obj) {
	var has = Object.prototype.hasOwnProperty || function () { return true };
	var keys = [];
	for (var key in obj) {
		if (has.call(obj, key)) keys.push(key);
	}
	return keys;
};

var seen = [];

function stringify(parent, key, node, level) {
	if (node && node.toJSON && typeof node.toJSON === 'function') {
		node = node.toJSON();
	}
	
	if (node === undefined) {
		return;
	}
	if (typeof node !== 'object' || node === null) {
		return JSON.stringify(node);
	}
	if (isArray(node)) {
		var out = [];
		for (var i = 0; i < node.length; i++) {
			var item = stringify(node, i, node[i], level+1) || JSON.stringify(null);
			out.push(item);
		}
		return '[' + out.join(', ') + ']';
	} else {
		if (seen.indexOf(node) !== -1) {
			throw new TypeError('Converting circular structure to JSON');
		} else {
			seen.push(node);
		}
		
		var keys = objectKeys(node).sort();
		var out = [];
		for (var i = 0; i < keys.length; i++) {
			var key = keys[i];
			var value = stringify(node, key, node[key], level+1);
			
			if(!value) {
				continue;
			}
			
			var keyValue = JSON.stringify(key) + ': ' + value;
			out.push(keyValue);
		}
		seen.splice(seen.indexOf(node), 1);
		return '{' + out.join(', ') + '}';
	}
};

function stringify_main(obj) {
	return stringify({ '': obj }, '', obj, 0);
}
