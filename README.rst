.. image:: https://travis-ci.org/karolyi/py3-validate-email.svg?branch=master
    :target: https://travis-ci.org/karolyi/py3-validate-email
.. image:: https://bmc-cdn.nyc3.digitaloceanspaces.com/BMC-button-images/custom_images/orange_img.png
    :target: https://buymeacoff.ee/karolyi

============================
py3-validate-email
============================

py3-validate-email is a package for Python that check if an email is valid, not blacklisted, properly formatted and really exists.

This module is for Python 3.6 and above!

INSTALLATION
============================

You can install the package with pip:

    pip install py3-validate-email


USAGE
============================

Basic usage::

    from validate_email import validate_email
    is_valid = validate_email(email_address='example@example.com', check_regex=True, check_mx=True, from_address='my@from.addr.ess', helo_host='my.host.name', smtp_timeout=10, dns_timeout=10, use_blacklist=True)

:code:`check_regex` will check will the email address has a valid structure and defaults to True

:code:`check_mx`: check the mx-records and check whether the email actually exists

:code:`from_address`: the email address the probe will be sent from,

:code:`helo_host`: the host to use in SMTP HELO when checking for an email,

:code:`smtp_timeout`: seconds until SMTP timeout

:code:`dns_timeout`: seconds until DNS timeout

:code:`use_blacklist`: use the blacklist of domains downloaded from https://github.com/martenson/disposable-email-domains

Auto-updater
============================
The package contains an auto-updater for downloading and updating the built-in blacklist.txt. It will run on each module load (and installation), but will try to update the content if the file is older than 5 days, and if the content is not the same that's already downloaded.

TODOs and BUGS
============================
See: https://github.com/karolyi/py3-validate-email/issues
