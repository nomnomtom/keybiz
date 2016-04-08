## Description

## LDAP Settings
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

## Required Packages

* ``django_auth_ldap``
* ``python-ldap``
* ``gpg`` >= GPG 1.2.2rc1
