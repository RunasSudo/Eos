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

import eos_sgjjr.models
import eos_core.admin
import eos_core.libobjects

import django.contrib.admin
import django.core.exceptions
import django.core.urlresolvers
import django.forms
import django.utils.html
import django.utils.safestring
import django.utils.timezone

import datetime

class SGJJRTrusteeInline(django.contrib.admin.TabularInline):
	model = eos_sgjjr.models.SGJJRTrustee
	
	readonly_fields = ['trustee_url']
	
	def trustee_url(self, obj):
		url = django.core.urlresolvers.reverse('trustee_home', args=[obj.id])
		return django.utils.safestring.mark_safe('<a href="' + url + '">Trustee URL</a>')

class ElectionWithTrusteesAdminForm(eos_core.admin.ElectionAdminForm):
	pass

class ElectionWithTrusteesAdmin(eos_core.admin.ElectionAdmin):
	form = ElectionWithTrusteesAdminForm
	
	inlines = [
		SGJJRTrusteeInline
	]

django.contrib.admin.site.register(eos_sgjjr.models.ElectionWithTrustees, ElectionWithTrusteesAdmin)
