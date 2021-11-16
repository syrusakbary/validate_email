[![](https://app.travis-ci.com/karolyi/py3-validate-email.svg?branch=master "Travis status")](https://app.travis-ci.com/karolyi/py3-validate-email)
[![](https://bmc-cdn.nyc3.digitaloceanspaces.com/BMC-button-images/custom_images/orange_img.png "Buy me a coffee!")](https://buymeacoff.ee/karolyi)

# py3-validate-email

py3-validate-email is a package for Python that check if an email is valid, not blacklisted, properly formatted and really exists.

This module is for Python 3.6 and above!

## INSTALLATION

You can install the package with pip:

    python -m pip install py3-validate-email

## USAGE

Basic usage:

    from validate_email import validate_email
    is_valid = validate_email(
        email_address='example@example.com',
        check_format=True,
        check_blacklist=True,
        check_dns=True,
        dns_timeout=10,
        check_smtp=True,
        smtp_timeout=10,
        smtp_helo_host='my.host.name',
        smtp_from_address='my@from.addr.ess',
        smtp_skip_tls=False,
        smtp_tls_context=None,
        smtp_debug=False)

### Parameters

`email_address`: the email address to check

`check_format`: check whether the email address has a valid structure; defaults to `True`

`check_blacklist`: check the email against the blacklist of domains downloaded from <https://github.com/disposable-email-domains/disposable-email-domains>; defaults to `True`

`check_dns`: check the DNS mx-records, defaults to `True`

`dns_timeout`: seconds until DNS timeout; defaults to 10 seconds

`check_smtp`: check whether the email actually exists by initiating an SMTP conversation; defaults to `True`

`smtp_timeout`: seconds until SMTP timeout; defaults to 10 seconds

`smtp_helo_host`: the hostname to use in SMTP HELO/EHLO; if set to `None` (the default), the fully qualified domain name of the local host is used

`smtp_from_address`: the email address used for the sender in the SMTP conversation; if set to `None` (the default), the email_address parameter is used as the sender as well

`smtp_skip_tls`: skip the TLS negotiation with the server, even when available. defaults to `False`

`smtp_tls_context`: an SSLContext to use with the TLS negotiation when the server supports it. defaults to `None`

`smtp_debug`: activate smtplib's debug output which always goes to stderr; defaults to `False`

### Result

The function `validate_email()` returns the following results:

_`True`_
  All requested checks were successful for the given email address.

_`False`_
  At least one of the requested checks failed for the given email address.

_`None`_
  None of the requested checks failed, but at least one of them yielded an ambiguous result. Currently, the SMTP check is the only check which can actually yield an ambiguous result.

### Getting more information

The function `validate_email_or_fail()` works exactly like `validate_email()`, except that it raises an exception in the case of validation failure and ambiguous result instead of returning `False` or `None`, respectively.

All these exceptions descend from `EmailValidationError`. Please see below for the exact exceptions raised by the various checks. Note that all exception classes are defined in the module `validate_email.exceptions`.

Please note that `SMTPTemporaryError` indicates an ambiguous check result rather than a check failure, so if you use `validate_email_or_fail()`, you probably want to catch this exception.

## The checks

By default, all checks are enabled, but each of them can be disabled by one of the `check_...` parameters. Note that, however, `check_smtp` implies `check_dns`.

### `check_format`

Check whether the given email address conforms to the general format requirements of valid email addresses.

validate_email_or_fail() raises AddressFormatError on any failure of this test.

### `check_blacklist`

Check whether the domain part of the given email address (the part behind the "@" is known as a disposable and temporary email address domain. These are often used to register dummy users in order to spam or abuse some services.

A list of such domains is maintained at <https://github.com/disposable-email-domains/disposable-email-domains>, and this module uses that list.

`validate_email_or_fail()` raises `DomainBlacklistedError` if the email address belongs to a blacklisted domain.

### `check_dns`

Check whether there is a valid list of servers responsible for delivering emails to the given email address.

First, a DNS query is issued for the email address' domain to retrieve a list of all MX records. That list is then stripped of duplicates and malformatted entries. If at the end of this procedure, at least one valid MX record remains, the check is considered successful.

On failure of this check, `validate_email_or_fail()` raises one of the following exceptions, all of which descend from `DNSError`:

_`DomainNotFoundError`_
The domain of the email address cannot be found at all.

_`NoNameserverError`_
There is no nameserver for the domain.

_`DNSTimeoutError`_
A timeout occured when querying the nameserver. Note that the timeout period can be changed with the `dns_timeout` parameter.

_`DNSConfigurationError`_
The nameserver is misconfigured.

_`NoMXError`_
The nameserver does not list any MX records for the domain.

_`NoValidMXError`_
The nameserver lists MX records for the domain, but none of them is valid.

### `check_smtp`

Check whether the given email address exists by simulating an actual email delivery.

A connection to the SMTP server identified through the domain's MX record is established, and an SMTP conversation is initiated up to the point where the server confirms the existence of the email address. After that, instead of actually sending an email, the conversation is cancelled.

Unless you set `smtp_skip_tls` to `True`, the module will try to negotiate a TLS connection with STARTTLS, and silently fall back to an unencrypted SMTP connection if the server doesn't support it. Additionally, depending on your client configuration, the TLS negotiation might fail which will result in an ambiguous response for the given host as the module will be unable to communicate with the host after the negotiation fails. In trying to succeed, you can pass an `SSLContext` as an `smtp_tls_context` parameter, but remember that the server might still deny the negotiation based on how you set the `SSLContext` up, and based on its security settings as well.

If the SMTP server replies to the `RCPT TO` command with a code `250` (success) response, the check is considered successful.

If the SMTP server replies with a code `5xx` (permanent error) response at any point in the conversation, the check is considered failed.

If the SMTP server cannot be connected, unexpectedly closes the connection, or replies with a code `4xx` (temporary error) at any stage of the conversation, the check is considered ambiguous.

If there is more than one valid MX record for the domain, they are tried in order of priority until the first time the check is either successful or failed. Only in case of an ambiguous check result, the next server is tried, and only if the check result is ambiguous for all servers, the overall check is considered ambiguous as well.

On failure of this check or on ambiguous result, `validate_email_or_fail()` raises one of the following exceptions, all of which descend from `SMTPError`:

_`AddressNotDeliverableError`_
The SMTP server permanently refused the email address. Technically, this means that the server replied to the `RCPT TO` command with a code 5xx response.

_`SMTPCommunicationError`_
The SMTP server refused to even let us get to the point where we could ask it about the email address. Technically, this means that the server sent a code `5xx` response either immediately after connection, or as a reply to the `EHLO` (or `HELO`) or `MAIL FROM` commands.

_`SMTPTemporaryError`_
A temporary error occured during the check for all available MX servers. This is considered an ambiguous check result. For example, greylisting is a frequent cause for this. Make sure you check the contents of the message.

All of the above three exceptions provide further details about the error response(s) in the exception's instance variable error_messages.

## Auto-updater

The package contains an auto-updater for downloading and updating the built-in blacklist.txt. It will run on each module load (and installation), but will try to update the content only if the file is older than 5 days, and if the content is not the same that's already downloaded.

The update can be triggered manually:

    from validate_email.updater import update_builtin_blacklist

    update_builtin_blacklist(
        force: bool = False,
        background: bool = True,
        callback: Callable = None
    ) -> Optional[Thread]

`force`: forces the update even if the downloaded/installed file is fresh enough.

`background`: starts the update in a `Thread` so it won't make your code hang while it's updating. If you set this to `True`, the function will return the Thread used for starting the update so you can `join()` it if necessary.

`callback`: An optional Callable (function/method) to be called when the update is done.

# Read the [FAQ](https://gitea.ksol.io/karolyi/py3-validate-email/src/branch/master/FAQ.md)!

