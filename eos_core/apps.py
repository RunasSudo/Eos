import django.apps
import django.contrib.staticfiles.apps

class EosCoreConfig(django.apps.AppConfig):
	name = 'eos_core'

class EosStaticFilesConfig(django.contrib.staticfiles.apps.StaticFilesConfig):
	ignore_patterns = ['bower.json']
