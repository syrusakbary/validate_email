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

You can install the package with pip::

    python -m pip install py3-validate-email


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

The function :code:`validate_email_or_fail()` works exactly like :code:`validate_email`, except that it raises an exception in the case of validation failure instead of returning :code:`False`.

Auto-updater
============================
The package contains an auto-updater for downloading and updating the built-in blacklist.txt. It will run on each module load (and installation), but will try to update the content only if the file is older than 5 days, and if the content is not the same that's already downloaded.

The update can be triggered manually::

    from validate_email.updater import update_builtin_blacklist

    update_builtin_blacklist(force: bool = False, background: bool = True,
        callback: Callable = None) -> Optional[Thread]

:code:`force`: forces the update even if the downloaded/installed file is fresh enough.

:code:`background`: starts the update in a ``Thread`` so it won't make your code hang while it's updating. If you set this to true, the function will return the Thread used for starting the update so you can ``join()`` it if necessary.

:code:`callback`: An optional `Callable` (function/method) to be called when the update is done.

TODOs and BUGS
============================
See: https://github.com/karolyi/py3-validate-email/issues
