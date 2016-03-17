from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
	url(r'^keycheck/', include('keycheck.urls')),
	url(r'^accounts/login', auth_views.login, {'template_name': 'keycheck/login.html'}, name='login'),
	url(r'^accounts/logout', auth_views.logout, name='logout'),
]
