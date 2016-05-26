from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
	url(r'^manage$', views.manage, name='manage'),
	url(r'^sign/(?P<keyId>[0-9]+)/$', views.sign, name='sign'),
	#url(r'^login$', 'django.contrib.auth.views.login', {'template_name': 'keycheck/login.html'}, name='login'),
]
