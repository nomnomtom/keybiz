from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
	url(r'^keycheck/', include('keycheck.urls')),
	url(r'^accounts/login', 'django.contrib.auth.views.login', {'template_name': 'keycheck/login.html'}, name='login'),
]
