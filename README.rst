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
    is_valid = validate_email(email_address='example@example.com', check_regex=True, check_mx=True, from_address='my@from.addr.ess', helo_host='my.host.name', smtp_timeout=10, dns_timeout=10, use_blacklist=True, debug=False)

:code:`check_regex` will check will the email address has a valid structure and defaults to True

:code:`check_mx`: check the mx-records and check whether the email actually exists

:code:`from_address`: the email address the probe will be sent from,

:code:`helo_host`: the host to use in SMTP HELO when checking for an email,

:code:`smtp_timeout`: seconds until SMTP timeout

:code:`dns_timeout`: seconds until DNS timeout

:code:`use_blacklist`: use the blacklist of domains downloaded from https://github.com/martenson/disposable-email-domains

:code:`debug`: emit debug messages while checking email

The function :code:`validate_email_or_fail()` works exactly like :code:`validate_email`, except that it raises an exception in the case of validation failure instead of returning :code:`False`.

The module will try to negotiate a TLS connection with STARTTLS, and silently fall back to an unencrypted SMTP connection if the server doesn't support it.

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

FAQ:
========
The module provides false positives:
------------------------------------
Some SMTP Servers (Yahoo's servers for example) are only rejecting nonexistent emails after the end of ``DATA`` command has been provided in the conversation with the server. This module only goes until the ``RCPT TO`` and says it's valid if it doesn't get rejected there, since the ``DATA`` part of the email is the email body itself. There's not much one can do with it, you have to accept false positives in the case of yahoo.com and some other providers.  I'm not sure if rejecting emails after the ``DATA`` command is a valid behavior based on the SMTP RFC, but I wouldn't wonder if not.

Everything gets rejected:
-------------------------
Check if you have port 25 access from your IP to the accepting server's IP. Even if you do, the server might use RBL's (spamhaus.org lists, for example), and your IP might get rejected because of being listed in one of the used lists by the email server. Your best bet is to use this module on another server that delivers emails, thus eliminating the chance of being blacklisted.

I can't check thousands of emails!
----------------------------------
This module is a tool; every tool can become a weapon if not used properly. In my case, I use this module to check email address validity at registration time, so not thousands at once. Doing so might make you (your IP) end up in one of the aforementioned blocklists, as providers will detect you as a possible spammer. In short, I would advise against your use case.

My email doesn't check out!
---------------------------
Run this code with the module installed (use your parameters within), and see the output::

    python -c 'import logging, sys; logging.basicConfig(stream=sys.stderr, level=logging.DEBUG); from validate_email import validate_email; print(validate_email(\'your.email@address.com\', check_mx=True, debug=True))'


If you still don't understand why your code doesn't work as expected by looking at the the logs, then (and only then) add an issue explaining your problem with a REPRODUCIBLE example, and the output of your test run.
