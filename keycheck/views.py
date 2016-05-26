from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from keycheck.forms import addKey
from keycheck.models import GpgKey, Mail
from utils import updateUserMails, makeAdmin

def index(request):
	'''
	the index view should give an overview of keybiz's capabilities and show
	some kind of login form. Whether or not a user is logged in should not
	matter.
	'''
	return render(request, 'keycheck/index.html', {})

@login_required
def manage(request):
	'''
	the manage view allows users to review their email addresses and uploaded
	keys. Users can upload a key which will be used to sign all the addresses
	that also are present to the system.
	'''
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
					for m in mails:
						m.save()
						m.sign(key)
				else:
					errmsg = "None of the key's uids matched your registered email addresses."
	else:
		form = addKey()
	return render(request, 'keycheck/manage.html', {'form': form, 'mail': mails, 'keymail': keymails, 'errmsg': errmsg})

@login_required
def sign(request, keyId, sign=None):
	gpgkey = GpgKey.objects.get(pk=keyId)
	userkey = [] #has the user an uid with this key attached?
	for m in Mail.objects.filter(user=request.user):
		if gpgkey in m.gpgkey.all():
			userkey.append(m)
	errmsg = None
	if userkey == []:
		errmsg = "Key not found."
	signKey = request.GET.get('sign', False)
	if signKey:
		for m in Mail.objects.filter(user=request.user):
			m.save()
			m.sign(gpgkey)
	elif not signKey:
		pass
	else:
		errmsg = "Error processing your request, please try again."
	return render(request, 'keycheck/sign.html', {'gpgkey': gpgkey, 'errmsg': errmsg, 'signKey': signKey})
