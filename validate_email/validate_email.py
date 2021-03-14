from logging import getLogger
from typing import Optional

from .dns_check import dns_check
from .domainlist_check import domainlist_check
from .email_address import EmailAddress
from .exceptions import (
    AddressFormatError, EmailValidationError, FromAddressFormatError,
    SMTPTemporaryError)
from .regex_check import regex_check
from .smtp_check import smtp_check

LOGGER = getLogger(name=__name__)

__all__ = ['validate_email', 'validate_email_or_fail']
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
    email_address: str, *, check_format: bool = True,
    check_blacklist: bool = True, check_dns: bool = True,
    dns_timeout: float = 10, check_smtp: bool = True,
    smtp_timeout: float = 10, smtp_helo_host: Optional[str] = None,
    smtp_from_address: Optional[str] = None, smtp_debug: bool = False
) -> Optional[bool]:
    """
    Return `True` if the email address validation is successful, `None`
    if the validation result is ambigious, and raise an exception if the
    validation fails.
    """
    email_address = EmailAddress(address=email_address)
    if check_format:
        regex_check(email_address=email_address)
    if check_blacklist:
        domainlist_check(email_address=email_address)
    if not check_dns and not check_smtp:  # check_smtp implies check_dns.
        return True
    mx_records = dns_check(email_address=email_address, timeout=dns_timeout)
    if not check_smtp:
        return True
    if smtp_from_address is not None:
        try:
            smtp_from_address = EmailAddress(address=smtp_from_address)
        except AddressFormatError:
            raise FromAddressFormatError
    return smtp_check(
        email_address=email_address, mx_records=mx_records,
        timeout=smtp_timeout, helo_host=smtp_helo_host,
        from_address=smtp_from_address, debug=smtp_debug)


def validate_email(email_address: str, **kwargs):
    """
    Return `True` or `False` depending if the email address exists
    or/and can be delivered.

    Return `None` if the result is ambigious.
    """
    try:
        return validate_email_or_fail(email_address, **kwargs)
    except SMTPTemporaryError as error:
        LOGGER.info(msg=f'Validation for {email_address!r} ambigious: {error}')
        return
    except EmailValidationError as error:
        LOGGER.info(msg=f'Validation for {email_address!r} failed: {error}')
        return False
