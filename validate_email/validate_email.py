from logging import getLogger
from typing import Optional

from .domainlist_check import domainlist_check
from .email_address import EmailAddress
from .exceptions import (
    AddressFormatError, EmailValidationError, FromAddressFormatError,
    SMTPTemporaryError)
from .mx_check import mx_check
from .regex_check import regex_check

LOGGER = getLogger(name=__name__)

__doc__ = """\
Verify the given email address by determining the SMTP servers
responsible for the domain and then asking them to deliver an email to
the address. Before the actual message is sent, the process is
interrupted.

PLEASE NOTE: Some email providers only tell the actual delivery failure
AFTER having delivered the body which this module doesn't, while others
simply accept everything and send a bounce notification later. Hence, a
100% proper response is not guaranteed.
"""


def validate_email_or_fail(
        email_address: str, check_regex: bool = True, check_mx: bool = True,
        from_address: Optional[str] = None, helo_host: Optional[str] = None,
        smtp_timeout: int = 10, dns_timeout: int = 10,
        use_blacklist: bool = True, debug: bool = False,
        skip_smtp: bool = False) -> Optional[bool]:
    """
    Return `True` if the email address validation is successful, `None`
    if the validation result is ambigious, and raise an exception if the
    validation fails.
    """
    email_address = EmailAddress(address=email_address)
    if from_address is not None:
        try:
            from_address = EmailAddress(address=from_address)
        except AddressFormatError:
            raise FromAddressFormatError
    if check_regex:
        regex_check(address=email_address)
    if use_blacklist:
        domainlist_check(address=email_address)
    if not check_mx:
        return True
    return mx_check(
        email_address=email_address, from_address=from_address,
        helo_host=helo_host, smtp_timeout=smtp_timeout,
        dns_timeout=dns_timeout, skip_smtp=skip_smtp, debug=debug)


def validate_email(email_address: str, *args, **kwargs):
    """
    Return `True` or `False` depending if the email address exists
    or/and can be delivered.

    Return `None` if the result is ambigious.
    """
    try:
        return validate_email_or_fail(email_address, *args, **kwargs)
    except SMTPTemporaryError as error:
        LOGGER.info(msg=f'Validation for {email_address!r} ambigious: {error}')
        return
    except EmailValidationError as error:
        LOGGER.info(msg=f'Validation for {email_address!r} failed: {error}')
        return False
