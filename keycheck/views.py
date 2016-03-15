from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

def index(request):
	return render(request, 'keycheck/index.html', {})

@login_required
def manage(request):
	mail = request.user.ldap_user.attrs['mail']
	return render(request, 'keycheck/manage.html', {'mail': mail})
