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

function generateEncryptedVote(election, answers, should_do_fingerprint) {
	encrypted_answers = [];
	for (var q_num = 0; q_num < answers.length; q_num++) {
		answer_json = answers[q_num];
		answer = eosjs.eos.core.objects.__all__.EosObject.deserialise_and_unwrap(answer_json, null);
		encrypted_answer = eosjs.eos.psr.election.__all__.BlockEncryptedAnswer.encrypt(election.public_key, answer, election.questions.__getitem__(q_num).max_bits() + 32); // +32 bits for the length
		encrypted_answers.push(eosjs.eos.core.objects.__all__.EosObject.serialise_and_wrap(encrypted_answer, null));
	}
	
	postMessage({
		encrypted_answers: encrypted_answers
	});
}

onmessage = function(msg) {
	if (!isLibrariesLoaded) {
		importScripts(
			msg.data.static_base_url + "js/eosjs.js"
		);
		isLibrariesLoaded = true;
	}
	
	if (msg.data.action === "generateEncryptedVote") {
		msg.data.election = eosjs.eos.core.objects.__all__.EosObject.deserialise_and_unwrap(msg.data.election, null);
		
		generateEncryptedVote(msg.data.election, msg.data.answers);
	} else {
		throw "Unknown action: " + msg.data.action;
	}
}
