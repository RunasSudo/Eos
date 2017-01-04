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

from django.http import HttpResponse
from django.shortcuts import render

from .eos_crypto.bigint import BigInt
from .eos_crypto.elgamal import ElGamalPrivateKey, ElGamalCiphertext
from .models import Message

def index(request):
	if len(ElGamalPrivateKey.objects.all()) > 0:
		key = ElGamalPrivateKey.objects.all()[0]
	else:
		key = ElGamalPrivateKey.generate()
		key.save()
	
	if request.method == 'POST':
		c = ElGamalCiphertext(BigInt(request.POST['gamma']), BigInt(request.POST['delta']))
		m = key.decrypt(c)
		message = Message(m=m)
		message.save()
	
	messages = Message.objects.all()
	
	return render(request, 'index.html', {'messages': messages, 'key': key.public_key })
