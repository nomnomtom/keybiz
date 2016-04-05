from keycheck.models import Mail

def updateUserMails(request):
	ldapMails = request.user.ldap_user.attrs['mail']
	userMails = Mail.objects.filter(user=request.user)
	newMails = ldapMails

	# find new mail addresses
	for m in userMails:
		if m.address in ldapMails:
			newMails.remove(m.address)

	# add mail objects
	for m in newMails:
		newmail = Mail(user=request.user, address=m)
		newmail.save()

	return newMails
