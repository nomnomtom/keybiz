from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from keycheck.forms import addKey
from keycheck.models import GpgKey, Mail
from utils import updateUserMails

def index(request):
	return render(request, 'keycheck/index.html', {})

@login_required
def manage(request):
	form = None
	errmsg = None
	keymails = []
	newmails = updateUserMails(request)
	mails = Mail.objects.filter(user=request.user)
	if request.method == "POST":
		form = addKey(request.POST)
		if form.is_valid():
			key = GpgKey(keydata=form.cleaned_data['keydata'])
			keymails = key.getMails()
			if keymails == []:
				errmsg = "Could not extract mails from key, have you added your addresses to that key?"
			elif keymails is False:
				errmsg = "Could not read GPG data, is that key valid?"
			else:
				# save mails and add key to mails
				keycount = 0
				for m in mails:
					if str(m) in keymails and key not in m.gpgkey.all():
						if keycount == 0:
							key.save() #save key iff we found an address.
						m.gpgkey.add(key)
						keycount += 1
				if keycount > 0:
					m.save()
				else:
					errmsg = "None of the key's uids matched your registered email addresses."
	else:
		form = addKey()
		keymails = []
	return render(request, 'keycheck/manage.html', {'form': form, 'mail': mails, 'keymail': keymails, 'errmsg': errmsg})
