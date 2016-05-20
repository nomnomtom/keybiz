# KEYBIZ

## What is Keybiz

Keybiz allows you to upload your public GnuPG keys in a web interface and signs all uids that are known through an authentication back end. The signed key will be uploaded to a key server. 

Users should 
## Installation

Keybiz runs as a web application and requires a web server with wsgi capabilities (e.g. apache2). For installation instructions regarding wsgi applications with your web server refer to their read me documents.

Since keybiz deals with sensitive data, an enforced encrypted HTTP connection is recommended.

### Required Packages

You need a LDAP server, a web server and a data base.
#### From your package manager

* ``python`` >= 2.7
* ``python-dev``
* ``libldap2-dev``
* ``gnupg`` >= 1.2.2rc1

#### From pip
* ``django``
* ``python-ldap``
* ``django_auth_ldap``

### Webserver Setup

See <https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/modwsgi/>. The following is an example nginx configuration. Install nginx (e.g. ``apt install -y nginx``) and uwsgi with pip (e.g. ``pip install uwsgi``). You'll also need a SSL certificate chain for HTTPS connections.

```
server {
    listen 80;
    server_name sks.example.com keys.example.com;
    location /keycheck {
        include         uwsgi_params;
        uwsgi_pass      localhost:45555;
    }
    location / {
        return 301 /keycheck;
    }

}
server {
    listen 443 ssl;
    server_name sks.example.com keys.example.com;
    ssl_certificate /etc/ssl/certs/sks.example.com.crt;
    ssl_certificate_key /etc/ssl/private/sks.example.com.key;
    location /accounts {
        include         uwsgi_params;
        uwsgi_pass      localhost:45555;
    }
    location /keycheck {
        include         uwsgi_params;
        uwsgi_pass      localhost:45555;
    }
    location /admin {
        include         uwsgi_params;
        uwsgi_pass      localhost:45555;
    }
    location / {
        return 301 /keycheck;
    }
}
```

This configuration assumes keybiz will redirect any unencrypted communication from either <http://sks.example.com> or <http://keys.example.com> to their https counter parts. This is enabled by default in ``settings.py``. It also assumes a running uwsgi server on port 45555. An example matching uwsgi configuration (e.g. ``/etc/uwsgi/keybiz.cnf``) follows:

```
[uwsgi]
chdir=/opt/keybiz/
module=keybiz.wsgi:application
master=True
env DJANGO_SETTINGS_MODULE=keybiz.settings
pidfile=/tmp/keybiz.pid
vacuum=True
max-requests=5000
daemonize=/var/log/uwsgi/keybiz.log
socket=127.0.0.1:45555
processes=5
```

This configuration assumes KeyBiz is installed in /opt/keybiz/. See the uwsgi documentation for further configuration options. Add ``uwsgi --ini /etc/uwsgi/keybiz.cnf`` to your ``/etc/rc.local`` to start the uwsgi server at boot. Run that command, to start the server without rebooting. To restart, run ``uwsgi --reload /tmp/keybiz.pid``. You need to restart after each configuration change.

After starting nginx, you should now be able to see the KeyBiz home page in your web browser. If you see an error message, you may need to set up a data base.

### DB Setup
A wide range of databases are supported. As KeyBiz will probably not cause heavy load on your database backend, no special considerations need to be made. KeyBiz supports PostgreSQL, MySQL, Oracle and SQLite. For installation instructions please refer to <https://docs.djangoproject.com/ja/1.9/ref/databases/>.

The easiest is a SQLite data base. For more complex cases, a PostgreSQL setup will be outlined.

First, you have to install postgresql with your package manager. Also, you have to install the python binding with pip, e.g. ``pip install psycopg2``. After that, you have to set up a data base for KeyBiz and adjust the ``settings.py``.

To set up a data base called keybiz, run the following comands

```
sudo su - postgres
createdb keybiz
createuser -P keybiz
```

...and answer all promts.

```
psql
GRANT ALL PRIVILEGES ON DATABASE keybiz TO keybiz;
```

This allows the newly created user to actually use the data base. Now adjust the data base settings in ``settings.py``

```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'keybiz',
        'USER': 'keybiz',
        'PASSWORD': 'supersecretpassword (but not this one)',
        'HOST': 'localhost',
        'PORT': '',
    }
}
```

leave ``PORT`` empty for default.

Now you need to sync KeyBiz with the data base like so

```
python /opt/keybiz/manage.py migrate
```

### GPG Setup

For signing, a secret key without password is required. This key has to be the standard signing key. Keybiz supports a separate key ring for its operations.

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
Make sure you enter the correct base for the user tree

Additionally, the LDAP auth back end is required:

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

## License

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

## Contact

email: <tom@inet.tu-berlin.de>
