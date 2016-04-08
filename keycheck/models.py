from __future__ import unicode_literals, print_function

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from subprocess import Popen, PIPE
from re import match
from tempfile import NamedTemporaryFile


class GpgKey(models.Model):
	keydata = models.TextField(unique=True)

	def getKeyID(self):
		''' return long key id '''
		p = Popen([settings.GPG_BIN, '--with-fingerprint', '--keyid-format', 'LONG'], stdout=PIPE, stderr=PIPE, stdin=PIPE)
		out, err = p.communicate(input=self.keydata)
		if out != "":
			out = out.split("\n")[0] #id is in first line
			groups = match(r"pub.*\d+.\/([A-Z0-9]{16})", out)
			if groups:
				return u"%s"% (groups.group(1))
			else:
				return False
		else:
			return u"%s"% (err)

	def listKey(self):
		''' 
		output of gpg --list-key <keyid> as a list of one line per 
		element 
		'''
		keyid = self.getKeyID()
		if keyid is False:
			return False
		p = Popen([settings.GPG_BIN, '--list-key', keyid], stdout=PIPE, stderr=PIPE)
		out, err = p.communicate()
		if out != '':
			return out.split("\n")
		else:
			return False

	def getMails(self):
		'''
		return a list of email addresses from uids
		'''
		mails = []
		key = self.listKey()
		if key is False:
			return False
		for k in key:
			groups = match(r"uid.*<(.*)>", k)
			if groups:
				mails.append(groups.group(1))
		return mails

	def save(self, *args, **kwargs):
		'''override djangos save method to add key to keyring'''
		tempkey = NamedTemporaryFile()
		try:
			tempkey.write(self.keydata)
			p = Popen([settings.GPG_BIN, '--import', tempkey.name])
			p.communicate() # wait for p to finish
		finally:
			tempkey.close()
		super(Model, self).save(*args, **kwargs)

	def __unicode__(self):
		return self.getKeyID()

class Mail(models.Model):
	user = models.ForeignKey(User)
	address = models.EmailField()
	gpgkey = models.ManyToManyField(GpgKey) # add keys with mailobj.add(keyobj)
	#uploaded = [] # list of key ids that signed the email address

	def sign(self, key):
		return True

	def __unicode__(self):
		return self.address
