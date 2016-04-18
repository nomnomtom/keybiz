from keycheck.models import Mail
from django.conf import settings
from django.contrib.auth.models import User
import logging

def updateUserMails(request):
	'''
	compare user mail addresses in ldap and already saved mails and add new
	addresses to the database
	'''
	logger = logging.getLogger('keybiz')
	ldapMails = []
	for mailattr in settings.AUTH_LDAP_MAIL_ATTRS:
		ldapMails += request.user.ldap_user.attrs[mailattr]
	ldapMails = list(set(ldapMails)) # make them unique
	userMails = Mail.objects.filter(user=request.user)
	newMails = ldapMails

	# find new mail addresses
	for m in userMails:
		if m.address in ldapMails:
			newMails.remove(m.address)
	if newMails:
		logger.debug("Found new mails for %s: %s" % (request.user, ", ".join(newMails)))

	# add mail objects
	for m in newMails:
		newmail = Mail(user=request.user, address=m)
		newmail.save()

	return newMails

def makeAdmin(request):
	adminlist = settings.USER_ADMINLIST
	if str(request.user) in adminlist:
		user = User.objects.get(username=str(request.user))
		user.is_superuser = True
		user.save()
