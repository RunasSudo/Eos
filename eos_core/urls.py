from django.conf.urls import url

from . import views

urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^(?P<election_id>[0-9a-f-]+)$$', views.election_json, name='election_json'),
]
