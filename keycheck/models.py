from __future__ import unicode_literals, print_function

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from subprocess import Popen, PIPE
from re import match, search
from tempfile import NamedTemporaryFile


class GpgKey(models.Model):
	keydata = models.TextField(unique=True)

	def __init__(self, *args, **kwargs):
		super(GpgKey, self).__init__(*args, **kwargs)
		# TODO: only import if key doesn't exist
		tempkey = NamedTemporaryFile(delete=False)
		try:
			tempkey.write(self.keydata)
			tempkey.close() # we need to close this so the data is written >.<
			cmd = self.GPGCommand('--import', tempkey.name)
			p = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE) # import key to keyring
			out, err = p.communicate() # wait for p to finish
		finally:
			tempkey.close()


	def getKeyID(self):
		''' return long key id '''
		cmd = self.GPGCommand('--with-fingerprint', '--keyid-format', 'LONG')
		p = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE)
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
		cmd = self.GPGCommand('--list-key', keyid)
		p = Popen(cmd, stdout=PIPE, stderr=PIPE)
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
			groups = match(r"uid.*<(.*)>", k) # mails are in lines starting with uid and are enclosed by <> at the very end
			if groups:
				mails.append(groups.group(1))
		return mails

	def save(self, *args, **kwargs):
		'''
		override djangos save method to add key to keyring
		'''
		super(GpgKey, self).save(*args, **kwargs)

	def sendKey(self):
		'''send myself to a key server'''
		cmd = self.GPGCommand('--send-key', str(self))
		p = Popen(cmd, stdout=PIPE, stderr=PIPE)
		out, err = p.communicate()

		return True

	def GPGCommand(self, *args):
		cmd = [settings.GPG_BIN]
		cmd += self._getGPGAdditionalOptions()
		cmd += list(args)
		return cmd

	def _getGPGAdditionalOptions(self):
		opts = []
		if hasattr(settings, 'GPG_KEYSERVER'):
			opts.append('--keyserver')
			opts.append(settings.GPG_KEYSERVER)
		if hasattr(settings, 'GPG_KEYRING_FILE') and settings.GPG_KEYRING_FILE != '':
			opts.append('--no-default-keyring')
			opts.append('--keyring')
			opts.append(settings.GPG_KEYRING_FILE)
		return opts

	def __unicode__(self):
		return self.getKeyID()

class Mail(models.Model):
	user = models.ForeignKey(User)
	address = models.EmailField()
	gpgkey = models.ManyToManyField(GpgKey) #make sure you sign this uid before adding

	def sign(self, key):
		if key not in self.gpgkey.all():
			return False

		# find uid number
		uidlist = [] # list of uids without other key stuff
		myuid = 0 # uids start at 1
		for l in key.listKey():
			if search(r"^uid", l):
				uidlist.append(l)
		for i,l in enumerate(uidlist):
			if str(self) in l:
				myuid = i+1
				break
		
		if myuid == 0:
			return False
		else:
			# "gpg --default-cert-check-level 3 --edit-key 8E3DDB55C67FFA78 uid 3 sign save" and enter y
			cmd = key.GPGCommand('--yes', '--batch', '--default-cert-check-level', '3', '--edit-key', str(key), 'uid', str(myuid), 'sign', 'save')
			p = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE)
			#yes = Popen(['yes', 'y'], stdout=p.stdin)
			out, err = p.communicate('yes')
			#yes.wait()

			# upload to key server
			key.sendKey()
			return True

	def __unicode__(self):
		return self.address
