from logging import getLogger
from typing import Optional

from .domainlist_check import domainlist_check
from .email_address import EmailAddress
from .exceptions import (
    AddressFormatError, EmailValidationError, FromAddressFormatError)
from .mx_check import mx_check
from .regex_check import regex_check

LOGGER = getLogger(name=__name__)


def validate_email_or_fail(
        email_address: str, check_regex: bool = True, check_mx: bool = True,
        from_address: Optional[str] = None, helo_host: Optional[str] = None,
        smtp_timeout: int = 10, dns_timeout: int = 10,
        use_blacklist: bool = True, debug: bool = False) -> Optional[bool]:
    """
    Return `True` if the email address validation is successful, `None` if the
    validation result is ambigious, and raise an exception if the validation
    fails.
    """
    email_address = EmailAddress(email_address)
    if from_address is not None:
        try:
            from_address = EmailAddress(from_address)
        except AddressFormatError:
            raise FromAddressFormatError

    if check_regex:
        regex_check(email_address)
    if use_blacklist:
        domainlist_check(email_address)
    if not check_mx:
        return True
    return mx_check(
        email_address=email_address, from_address=from_address,
        helo_host=helo_host, smtp_timeout=smtp_timeout,
        dns_timeout=dns_timeout, debug=debug)


def validate_email(email_address: str, *args, **kwargs):
    """
    Return `True` or `False` depending if the email address exists
    or/and can be delivered.

    Return `None` if the result is ambigious.
    """
    try:
        return validate_email_or_fail(email_address, *args, **kwargs)
    except EmailValidationError as error:
        message = f'Validation for {email_address!r} failed: {error}'
        LOGGER.warning(msg=message)
        return False
