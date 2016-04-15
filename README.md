## Installation

Keybiz runs as a web application and requires a web server with wsgi capabilities (e.g. apache2). For installation instructions regarding wsgi applications with your web server refer to their readme documents.

Since keybiz deals with sensitive data, an enforced encrypted http connection is recommended.

### Required Packages

* ``python`` >= 2.6
* ``python-django``
* ``python-ldap``
* ``gpg`` >= GPG 1.2.2rc1
* ``django_auth_ldap``

### LDAP Settings
The ``settings.py`` requires additional settings for LDAP. The following is an example configuration that tries find the user without bind:

``
import ldap
from django_auth_ldap.config import LDAPSearch

AUTH_LDAP_SERVER_URI = "ldapi:///"
AUTH_LDAP_BIND_DN = ""
AUTH_LDAP_BIND_PASSWORD = ""
AUTH_LDAP_USER_SEARCH = LDAPSearch("ou=users,dc=gytha,dc=dn", ldap.SCOPE_SUBTREE, "(uid=%(user)s)")
``

Additionally, the LDAP auth backend is required.

``
AUTHENTICATION_BACKENDS = (
    'django_auth_ldap.backend.LDAPBackend',
)
``

### GPG Settings

``GPG_BIN='/usr/bin/gpg'``
Path to your GnuPG binary

``GPG_KEYRING_FILE='/var/run/django/mykeyring``
Optional keyring file, comment out to use standard key ring

``GPG_KEYSERVER='hkp://keys.gnupg.net'``
Optional keyserver, comment out to use standard key server

