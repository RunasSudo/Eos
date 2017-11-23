/*
	Eos - Verifiable elections
	Copyright © 2017  RunasSudo (Yingtong Li)
	
	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU Affero General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.
	
	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU Affero General Public License for more details.
	
	You should have received a copy of the GNU Affero General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

window = self; // Workaround for libraries
isLibrariesLoaded = false;

function generateEncryptedVote(election, selections) {
	encryptedVote = eos_js.eos_core.objects.__all__.PlaintextVote({ "choices": selections, "election_uuid": election.id, "election_hash": election.hash() });
	
	postMessage(eos_js.eos_core.libobjects.__all__.EosObject.serialise_and_wrap(encryptedVote, null));
}

onmessage = function(msg) {
	if (!isLibrariesLoaded) {
		importScripts(
			msg.data.static_base_url + "js/eosjs.js"
		);
		isLibrariesLoaded = true;
	}
	
	if (msg.data.action === "generateEncryptedVote") {
		msg.data.election = eosjs.eos.core.libobjects.__all__.EosObject.deserialise_and_unwrap(msg.data.election, null);
		
		generateEncryptedVote(msg.data.election, msg.data.selections);
	} else {
		throw "Unknown action: " + msg.data.action;
	}
}
