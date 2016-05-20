from __future__ import unicode_literals, print_function

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from subprocess import Popen, PIPE
from re import match, search
from tempfile import NamedTemporaryFile
from os import remove
import logging
logger = logging.getLogger("keybiz")

class GpgKey(models.Model):
	'''
	Models a GnuPG public key.

	The key is represented as an ascii string and will be imported to a keyring
	as soon as the object is created -- not on save. That means when you create
	a GpgKey object without saving it to the DB, you'll still import it to your
	keyring.

	A GpgKey model yields certain information about the key, including attached
	uids (i.e. email addresses) and offers a function for exporting signed keys
	to a hkp server.
	'''
	keydata = models.TextField(unique=True)

	def __init__(self, *args, **kwargs):
		'''
		creates GpgKey object and saves the key to a keyring file. 
		'''
		super(GpgKey, self).__init__(*args, **kwargs)
		# TODO: only import if key doesn't exist
		tempkey = NamedTemporaryFile(delete=False)
		try:
			tempkey.write(self.keydata)
			tempkey.close() # we need to close this so the data is written >.<
			cmd = self.GPGCommand('--import', tempkey.name)
			p = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE) # import key to keyring
			logger.info("Importing key to keyring")
			logger.debug("Command %s" % (" ".join(cmd)))
			out, err = p.communicate() # wait for p to finish
			if err != '':
				logger.warn("GPG error: %s" % (err))
			if out != '':
				logger.debug("GPG output: %s" % (out))
		finally:
			remove(tempkey.name)


	def getKeyID(self):
		''' return long key id from key data, not key ring'''
		cmd = self.GPGCommand('--with-fingerprint', '--keyid-format', 'LONG')
		p = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE)
		logger.debug("Checking key ID")
		logger.debug("Command %s" % (" ".join(cmd)))
		out, err = p.communicate(input=self.keydata)
		if out != "":
			logger.debug("GPG output: %s" % (out))
			out = out.split("\n")[0] #id is in first line
			groups = match(r"pub.*\d+.\/([A-Z0-9]{16})", out)
			if groups:
				return u"%s"% (groups.group(1))
			else:
				logger.warn("Error reading KeyID")
				return False
		else:
			logger.warn("Error reading KeyID: %s" % (err))
			return False

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
			logger.warn("Could not list key %s from keyring: %s" % (keyid, err))
			return False

	def getMails(self):
		'''
		return a list of email addresses from uids
		'''
		mails = []
		key = self.listKey()
		if key is False:
			return False
			
		logger.debug("Trying to find mails in key %s" % (str(self)))
		for k in key:
			groups = match(r"uid.*<(.*)>", k) # mails are in lines starting with uid and are enclosed by <> at the very end
			if groups:
				mails.append(groups.group(1))
				logger.debug("Found mail address %s in key %s" % (groups.group(1), str(self)))
		return mails

	def sendKey(self):
		'''
		send self to a key server.

		this does not check whether or not the key is signed.
		'''
		logger.info("Sending key %s to hkp server" % (str(self)))
		cmd = self.GPGCommand('--send-key', str(self))
		logger.debug("Command %s" % (" ".join(cmd)))
		p = Popen(cmd, stdout=PIPE, stderr=PIPE)
		out, err = p.communicate()
		if out != '':
			logger.debug("GPG output: %s" % (out))
		if err != '':
			logger.debug("GPG errors: %s" % (err))

 		return True

	def GPGCommand(self, *args):
		'''
		helper function for creating a GPG command

		this will put options from settings first, then *args

		*args: list of strings without gpg that constitute the command,
		       will be added to arguments from settings
		'''
		cmd = [settings.GPG_BIN]
		cmd += self._getGPGAdditionalOptions()
		cmd += list(args)
		return cmd

	def _getGPGAdditionalOptions(self):
		'''
		return GPG args from settings
		'''
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
		'''
		return key id
		'''
		return self.getKeyID()

class Mail(models.Model):
	user = models.ForeignKey(User)
	address = models.EmailField()
	gpgkey = models.ManyToManyField(GpgKey) #make sure you sign this uid!

	def sign(self, key):
		if key not in self.gpgkey.all():
			logger.warn("Tried to sign %s with key %s which has no related uid" % (str(self), str(key)))
			return False

		# find uid number
		uidlist = [] # list of uid lines without other key stuff
		myuid = 0 # uids start at 1
		for l in key.listKey():
			if search(r"^uid", l):
				uidlist.append(l)
		for i,l in enumerate(uidlist):
			if str(self) in l: #FIXME: what if we have b@x and ab@x and we search for b@x?
				myuid = i+1
				logger.debug("Found uid %d for key %s and email address %s" % (myuid, str(key), str(self)))
				break
		
		if myuid == 0:
			logger.warn("Tried to sign email address %s with key %s, but found no matching uid" % (str(self), str(key)))
			return False
		else:
			# "gpg --default-cert-check-level 3 --edit-key 8E3DDB55C67FFA78 uid 3 sign save" and enter y
			cmd = key.GPGCommand('--yes', '--batch', '--default-cert-check-level', '3', '--edit-key', str(key), 'uid', str(myuid), 'sign', 'save')
			logger.info("Signing key %s 's uid %d" % (str(key), myuid))
			logger.debug("Command: %s" % (cmd))
			p = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE)
			out, err = p.communicate('yes')
			if out != '':
				logger.debug("GPG output: %s" % (out))
			if err != '':
				logger.warn("GPG error: %s" % (err))

			# upload to key server
			key.sendKey()
			return True

	def __unicode__(self):
		return self.address
