certbot-dns-dinahosting
=======================

Dinahosting_ DNS Authenticator plugin for Certbot

This plugin automates the process of completing a ``dns-01`` challenge by
creating, and subsequently removing, TXT records using the Dinahosting API.

.. _Dinahosting: https://dinahosting.com/
.. _certbot: https://certbot.eff.org/

Installation
------------

::

    pip install git+https://github.com/rdrgzlng/certbot-dns-dinahosting.git@master

or::

    pip3 install git+https://github.com/rdrgzlng/certbot-dns-dinahosting.git@master


Named Arguments
---------------

To start using DNS authentication for Dinahosting, pass the following arguments on
certbot's command line:

================================================================= ==============================================
``--authenticator certbot-dns-dinahosting:dns-dinahosting``       select the authenticator plugin (Required)

``--certbot-dns-dinahosting:dns-dinahosting-credentials``         dinahosting Remote User credentials
                                                                  INI file. (Required)

``--certbot-dns-dinahosting:dns-dinahosting-propagation-seconds`` | waiting time for DNS to propagate before asking
                                                                  | the ACME server to verify the DNS record.
                                                                  | (Default: 10, Recommended: >= 600)
================================================================= ==============================================

(Note that the verbose and seemingly redundant ``certbot-dns-dinahosting:`` prefix
is currently imposed by certbot for external plugins.)


Credentials
-----------

An example ``credentials.ini`` file:

.. code-block:: ini

   certbot_dns_dinahosting:dns_dinahosting_username = myremoteuser
   certbot_dns_dinahosting:dns_dinahosting_password = verysecureremoteuserpassword

The path to this file can be provided interactively or using the
``--certbot-dns-dinahosting:dns-dinahosting-credentials`` command-line argument. Certbot
records the path to this file for use during renewal, but does not store the
file's contents.

**CAUTION:** You should protect these API credentials as you would the
password to your Dinahosting account. Users who can read this file can use these
credentials to issue arbitrary API calls on your behalf. Users who can cause
Certbot to run using these credentials can complete a ``dns-01`` challenge to
acquire new certificates or revoke existing certificates for associated
domains, even if those domains aren't being managed by this server.

Certbot will emit a warning if it detects that the credentials file can be
accessed by other users on your system. The warning reads "Unsafe permissions
on credentials configuration file", followed by the path to the credentials
file. This warning will be emitted each time Certbot uses the credentials file,
including for renewal, and cannot be silenced except by addressing the issue
(e.g., by using a command like ``chmod 600`` to restrict access to the file).


Examples
--------

To acquire a certificate for ``example.com``

.. code-block:: bash

   certbot certonly \\
     --authenticator certbot-dns-dinahosting:dns-dinahosting \\
     --certbot-dns-dinahosting:dns-dinahosting-credentials ~/.secrets/certbot/dinahosting.ini \\
     -d example.com


To acquire a single certificate for both ``example.com`` and ``www.example.com``

.. code-block:: bash

   certbot certonly \\
     --authenticator certbot-dns-dinahosting:dns-dinahosting \\
     --certbot-dns-dinahosting:dns-dinahosting-credentials ~/.secrets/certbot/dinahosting.ini \\
     -d example.com \\
     -d www.example.com


To acquire a certificate for ``example.com``, waiting 60 seconds for DNS propagation

.. code-block:: bash

   certbot certonly \\
     --authenticator certbot-dns-dinahosting:dns-dinahosting \\
     --certbot-dns-dinahosting:dns-dinahosting-credentials ~/.secrets/certbot/dinahosting.ini \\
     --certbot-dns-dinahosting:dns-dinahosting-propagation-seconds 60 \\
     -d example.com


Docker
------

In order to create a docker container with a certbot-dns-dinahosting installation,
create an empty directory with the following ``Dockerfile``:

.. code-block:: docker

    FROM certbot/certbot
    RUN pip install git+https://github.com/rdrgzlng/certbot-dns-dinahosting.git@master

Proceed to build the image::

    docker build -t certbot/dns-dinahosting .

Once that's finished, the application can be run as follows::

    docker run --rm \
       -v /var/lib/letsencrypt:/var/lib/letsencrypt \
       -v /etc/letsencrypt:/etc/letsencrypt \
       --cap-drop=all \
       certbot/dns-dinahosting certonly \
       --authenticator certbot-dns-dinahosting:dns-dinahosting \
       --certbot-dns-dinahosting:dns-dinahosting-propagation-seconds 900 \
       --certbot-dns-dinahosting:dns-dinahosting-credentials \
           /etc/letsencrypt/.secrets/dinahosting.ini \
       --no-self-upgrade \
       --keep-until-expiring \
       --non-interactive \
       --expand \
       --server https://acme-v02.api.letsencrypt.org/directory \
       -d example.com \
       -d *.example.com

It is suggested to secure the folder as follows::

    chown root:root /etc/letsencrypt/.secrets
    chmod 600 /etc/letsencrypt/.secrets
