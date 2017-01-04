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

try:
	__pragma__('opov')
	IS_PYTHON = False
except Exception:
	IS_PYTHON = True
	def __pragma__(a):
		pass

if IS_PYTHON:
	__pragma__('skip')
	import django.db.models
	import eos_test.fields
	BaseModelClass = django.db.models.Model
	
	class BaseModelType(django.db.models.base.ModelBase):
		def __new__(meta, name, bases, attribs):
			cls = django.db.models.base.ModelBase.__new__(meta, name, bases, attribs)
			
			fields = attribs['__fields__']
			for field, ftype in fields:
				if ftype is int:
					django.db.models.IntegerField().contribute_to_class(cls, field)
				else:
					eos_test.fields.ObjectField(field_type=ftype).contribute_to_class(cls, field)
			
			return cls
		
		def __call__(meta, *args, **kwargs):
			#return super().__call__(meta, *args, **kwargs)
			return type.__call__(meta, *args, **kwargs)
	__pragma__('noskip')
else:
	# TNYI: No pow() support
	def pow(a, b, c=None):
		return a.__pow__(b, c)
	
	BaseModelClass = object
	
	class BaseModelType(type):
		def __new__(meta, name, bases, attribs):
			return type.__new__(meta, name, bases, attribs)
		
		def __call__(meta, *args, **kwargs):
			instance = type.__call__(meta, *args, **kwargs)
			
			fields = [field for field, ftype in instance.__fields__]
			for arg, val in kwargs:
				if arg in fields and not hasattr(instance, arg):
					setattr(instance, arg, val)
			
			return instance


from .bigint import BigInt

# TODO: Make fields
class CyclicGroup:
	def __init__(self, p, g):
		self.p = p
		self.g = g

# RFC 3526
DH_GROUPS = {
	2048: CyclicGroup(BigInt('FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497CEA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF', 16), BigInt(2))
}
KEY_SIZE = 2048

class ElGamalCiphertext:
	def __init__(self, gamma, delta):
		self.gamma = gamma
		self.delta = delta

class ElGamalPublicKey:
	__field_type__ = 'TextField'
	
	def __init__(self, g_a):
		self.g_a = g_a
	
	def encrypt(self, m):
		k = BigInt.crypto_random(1, DH_GROUPS[KEY_SIZE].p - 2)
		return ElGamalCiphertext(pow(DH_GROUPS[KEY_SIZE].g, k, DH_GROUPS[KEY_SIZE].p), (m * pow(self.g_a, k, DH_GROUPS[KEY_SIZE].p)) % DH_GROUPS[KEY_SIZE].p)
	
	
	@staticmethod
	def to_python(value):
		return ElGamalPublicKey(BigInt(value))
	
	@staticmethod
	def from_python(value):
		return str(value.g_a)

class ElGamalPrivateKey(BaseModelClass, metaclass=BaseModelType):
	__fields__ = [('public_key', ElGamalPublicKey), ('a', BigInt)]
	
	@classmethod
	def generate(cls):
		a = BigInt.crypto_random(1, DH_GROUPS[KEY_SIZE].p - 2)
		return cls(public_key=ElGamalPublicKey(pow(DH_GROUPS[KEY_SIZE].g, a, DH_GROUPS[KEY_SIZE].p)), a=a)
	
	def decrypt(self, c):
		gamma_nega = pow(c.gamma, DH_GROUPS[KEY_SIZE].p - 1 - self.a, DH_GROUPS[KEY_SIZE].p)
		return (gamma_nega * c.delta) % DH_GROUPS[KEY_SIZE].p
