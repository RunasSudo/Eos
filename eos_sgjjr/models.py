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

import eos_sgjjr.crypto

import eos_core.models
import eos_core.libobjects

class ElectionWithTrustees(eos_core.models.Election):
	class EosMeta:
		eos_name = 'eos_sgjjr.models.ElectionWithTrustees'
		eos_fields = eos_core.models.Election._eosmeta.eos_fields.__add__([
			eos_core.libobjects.EosField(list, 'trustees', linked_property='trustee_set'),
		])
	
	class Meta:
		verbose_name_plural = 'elections with trustees'
	
	def get_tabs(self):
		tabs = super().get_tabs()
		tabs.insert(next(i for i, v in enumerate(tabs) if v[1] == 'Questions') + 1, ('election_trustees', 'Trustees'))
		return tabs

class Trustee(eos_core.models.EosDictObjectModel):
	class EosMeta:
		abstract = True
		eos_fields = [
			eos_core.libobjects.EosField(eos_core.libobjects.uuid, 'id', primary_key=True, editable=False),
			eos_core.libobjects.EosField(ElectionWithTrustees, 'election', on_delete='CASCADE', serialised=False),
			eos_core.libobjects.EosField(int, 'order'),
		]
	
	class Meta:
		# This model must be concrete in order to provide a trustee_set or Trustee.objects manager
		#abstract = True
		ordering = ['order']
	
	objects = eos_core.models.InheritanceManager()

class DjangoAuthTrustee(Trustee):
	class EosMeta:
		abstract = True
		eos_fields = Trustee._eosmeta.eos_fields.__add__([
			eos_core.libobjects.EosField(int, 'auth_user_id'),
		])
	
	class Meta:
		abstract = True
	
	@property
	def name(self):
		if eos_core.is_python:
			__pragma__ = lambda x: None
			__pragma__('skip')
			import django.contrib.auth.models
			return django.contrib.auth.models.User.objects.get(id=self.auth_user_id).username
			__pragma__('noskip')
		else:
			return None

class SGJJRTrustee(DjangoAuthTrustee):
	class EosMeta:
		eos_name = 'eos_sgjjr.models.SGJJRTrustee'
		eos_fields = DjangoAuthTrustee._eosmeta.eos_fields.__add__([
			eos_core.libobjects.EosField(eos_sgjjr.crypto.TDH1PublicKey, 'public_key', nullable=True, editable=False),
		])
