# KEYBIZ

## What is Keybiz

Keybiz allows you to upload your public GnuPG keys in a web interface and signs all uids that are known through an authentication back end. The signed key will be uploaded to a key server. 

Users should 
## Installation

Keybiz runs as a web application and requires a web server with wsgi capabilities (e.g. apache2). For installation instructions regarding wsgi applications with your web server refer to their read me documents.

Since keybiz deals with sensitive data, an enforced encrypted HTTP connection is recommended.

### Webserver Setup

* <https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/modwsgi/>

### DB Setup
A wide range of databases are supported. As KeyBiz will probably not cause heavy load on your database backend, no special considerations need to be made. KeyBiz supports PostgreSQL, MySQL, Oracle and SQLite. For installation instructions please refer to <https://docs.djangoproject.com/ja/1.9/ref/databases/>.

### GPG Setup

For signing, a secret key without password is required. This key has to be the standard signing key. Keybiz supports a separate key ring for it's operations.

### Required Packages

* ``python`` >= 2.6
* ``python-django``
* ``python-ldap``
* ``gpg`` >= GPG 1.2.2rc1
* ``django_auth_ldap``

### LDAP Settings
The ``settings.py`` requires additional settings for LDAP. The following is an example configuration that tries find the user without bind:

```
import ldap
from django_auth_ldap.config import LDAPSearch

AUTH_LDAP_SERVER_URI = "ldapi:///"
AUTH_LDAP_BIND_DN = ""
AUTH_LDAP_BIND_PASSWORD = ""
AUTH_LDAP_USER_SEARCH = LDAPSearch("ou=users,dc=gytha,dc=dn", ldap.SCOPE_SUBTREE, "(uid=%(user)s)")
```

Additionally, the LDAP auth back end is required.

```
AUTHENTICATION_BACKENDS = (
    'django_auth_ldap.backend.LDAPBackend',
)
```

Note that keybiz *will not work* with other authentication backends. Please make sure you have your users authenticated according to common gpg signing practices before allowing them access to keybiz.

### GPG Settings

For GPG, additional settings are required in ``settings.py``.

``GPG_BIN='/usr/bin/gpg'``
Path to your GnuPG binary

``GPG_KEYRING_FILE='/var/run/django/mykeyring``
Optional key ring file, comment out to use standard key ring

``GPG_KEYSERVER='hkp://keys.gnupg.net'``
Optional key server, comment out to use standard key server


## Management

* admin interface
* log in first
