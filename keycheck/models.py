from __future__ import unicode_literals, print_function

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from subprocess import Popen, PIPE
from re import match, search
from tempfile import NamedTemporaryFile
from os import remove
import logging
import hashlib
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
	keydata = models.TextField(unique=False)
	keyhash = models.CharField(max_length=10,default="",unique=True)

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
			cmd = GpgKey.GPGCommand('--import', tempkey.name)
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

	def save(self, *args, **kwargs):
		self.keyhash = hashlib.md5(self.keydata).hexdigest()
		super(GpgKey, self).save(*args, **kwargs)


	def getKeyID(self):
		''' return long key id from key data, not key ring'''
		cmd = GpgKey.GPGCommand('--with-fingerprint', '--keyid-format', 'LONG')
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
		cmd = GpgKey.GPGCommand('--list-key', keyid)
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
		cmd = GpgKey.GPGCommand('--send-key', str(self))
		logger.debug("Command %s" % (" ".join(cmd)))
		p = Popen(cmd, stdout=PIPE, stderr=PIPE)
		out, err = p.communicate()
		if out != '':
			logger.debug("GPG output: %s" % (out))
		if err != '':
			logger.debug("GPG errors: %s" % (err))

 		return True

	@staticmethod
	def GPGCommand(*args):
		'''
		helper function for creating a GPG command

		this will put options from settings first, then *args

		*args: list of strings without gpg that constitute the command,
		       will be added to arguments from settings
		'''
		cmd = [settings.GPG_BIN]
		cmd += GpgKey._getGPGAdditionalOptions()
		cmd += list(args)
		return cmd

	@staticmethod
	def _getGPGAdditionalOptions():
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
		if hasattr(settings, 'GPG_DEFAULT_KEY'):
			opts.append('--default-key')
			opts.append(settings.GPG_DEFAULT_KEY)
		else:
			logger.error("Option GPG_DEFAULT_KEY not found in settings.py!")
		return opts

	def __unicode__(self):
		'''
		return key id
		'''
		return self.getKeyID()

class Mail(models.Model):
	"""
	Models an email address that has a user and some gpg keys.

	Mails can be signed, mainly. For that, they need an attached gpg 
	key. Signing the uid requires a newer GPG version, check the 
	README.md file for more information.
	"""
	user = models.ForeignKey(User)
	address = models.EmailField()
	gpgkey = models.ManyToManyField(GpgKey) #make sure you sign this uid!

	def _getServerKeyID(self):
		'''
		checks with the key server if a key with the uid is available.

		returns long key id or False
		'''
		logger.debug("Searching keyserver for uid %s" % (str(self)))
		cmd = GpgKey.GPGCommand('--keyid-format', 'long', '--batch', '--search-key', self.address)
		p = Popen(cmd, stdout=PIPE, stderr=PIPE)
		out,err = p.communicate("") #sometimes, batch doesn't to squad
		if out != "":
			founduid = False
			r = []
			for l in out.split("\n"):
				group = match(r"(\((d+)\))?.*<(.*@.*)>", l)
				guid = match(r"[\t ]+\d+ bit.*key ([A-Z0-9]+)", l)
				if (group):
					if group.groups()[-1] == self.address:
						founduid = True
				elif (founduid and guid):
					# we found the uid and now we have the key id
					r.append(guid.groups()[-1])
					founduid = False
			return r
		elif err != "":
			logger.warn(err)
		return False

	def _downloadKey(self, keyid):
		'''
		download keyid from keyserver to keyring and return True
		'''
		logger.info("downloading new public keys for %s" % (str(self)))
		cmd = GpgKey.GPGCommand('--batch', '--recv-key', keyid) #TODO: can we use --recv-keys for all ids?
		p = Popen(cmd, stdout=PIPE, stderr=PIPE)
		out,err = p.communicate()
		if out != "":
			logger.debug(out)
		if err != "":
			logger.warn(err)
		return True
	
	def _checkSigs(self, keyid):
		'''
		return true if GPG_DEFAULT_KEY from settings.py is found amongst 
		the signatures of keyid
		'''
		if not hasattr(settings, 'GPG_DEFAULT_KEY'):
			logger.error("Option GPG_DEFAULT_KEY not found in settings.py!")
			return False
		if len(settings.GPG_DEFAULT_KEY) == 8:
			cmd = GpgKey.GPGCommand('--batch', '--keyid-format', 'short', '--check-sigs', keyid)
		elif len(settings.GPG_DEFAULT_KEY) == 16:
			cmd = GpgKey.GPGCommand('--batch', '--keyid-format', 'long', '--check-sigs', keyid)
		else:
			return False
		logger.debug("Searching signatures in key uid %s" % (str(self)))
		logger.debug("GPG Command: %s" % (" ".join(cmd)))
		p = Popen(cmd, stdout=PIPE, stderr=PIPE)
		out,err = p.communicate()
		if out != "":
			founduid = False
			for l in out.split("\n"):
				group = match(r"^uid.*<(.*)>$", l)
				sigg = match(r"^sig.* +([A-Z0-9]+) [\d\-]+", l)
				if group:
					if group.groups()[-1] == self.address:
						logger.debug("Found uid in key, checking signatures...")
						founduid = True
					else:
						logger.debug("No matching signatures found: %s" % (out))
						founduid = False
				elif sigg and founduid:
					logger.debug("Checking signature %s" % (sigg.groups()[-1]))
					if sigg.groups()[-1] == settings.GPG_DEFAULT_KEY:
						return True
		elif err != "":
			logger.warn(err)
		return False

	def _importKeys(self):
		"""
		search keyserver for keys that are already signed and import them
		to local data base so users see them and don't need to upload key
		again
		"""
		# are any keys present on keyserver anyway?
		# gpg -batch --search-keys 'uid'
		uid = self._getServerKeyID()
		if uid != False and uid != []:
			# do we have any of these uids in our own db already?
			for g in self.gpgkey.all():
				gid = g.getKeyID()
				if gid in uid:
					uid.remove(gid)
			# download the rest
			for u in uid:
				self._downloadKey(u)
				if self._checkSigs(u) == True:
					# here we found a key on the server that is not in our db AND signed by us.
					cmd = GpgKey.GPGCommand('--batch', '--export', '--armor', u)
					p = Popen(cmd, stdout=PIPE, stderr=PIPE)
					out,err = p.communicate()
					if out != "":
						logger.info("Found new key %s on keyserver, importing for uid %s" % (u, str(self)))
						newkey = GpgKey(keydata=out)
						self.save()
						newkey.save()
						self.gpgkey.add(newkey)
						self.save()
					elif err != "":
						logger.warn("Found new key %s on keyserver, but could not import for uid %s: %s" % (u, str(self), err))
		else:
			# No key is not on keyserver, so probably nothing signed by us.
			return False

	def __init__(self, *args, **kwargs):
		'''
		creates Mail object and checks for existing signatures
		'''
		super(Mail, self).__init__(*args, **kwargs)
		self._importKeys()

	def sign(self, key):
		"""
		sign the uid with a key. If a uid is already signed, GPG should 
		throw an error, so nothing bad will happen.
		"""
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
			# "gpg --default-cert-check-level 3 --edit-key XXXXXXXXXXXXXX uid 3 sign save" and enter y
			cmd = GpgKey.GPGCommand('--yes', '--batch', '--default-cert-check-level', '3', '--edit-key', str(key), 'uid', str(myuid), 'sign', 'save')
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
