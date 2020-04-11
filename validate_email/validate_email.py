from logging import getLogger
from typing import Optional

from .domainlist_check import domainlist_check
from .exceptions import AddressFormatError, EmailValidationError
from .mx_check import mx_check
from .regex_check import regex_check

LOGGER = getLogger(name=__name__)


def validate_email_or_fail(
        email_address: str, check_regex: bool = True, check_mx: bool = True,
        from_address: Optional[str] = None, helo_host: Optional[str] = None,
        smtp_timeout: int = 10, dns_timeout: int = 10,
        use_blacklist: bool = True) -> Optional[bool]:
    """
    Return `True` if the email address validation is successful, `None` if the
    validation result is ambigious, and raise an exception if the validation
    fails.
    """
    if not email_address or '@' not in email_address:
        raise AddressFormatError
    user_part, domain_part = email_address.rsplit('@', 1)
    if check_regex:
        regex_check(user_part=user_part, domain_part=domain_part)
    if use_blacklist:
        domainlist_check(user_part=user_part, domain_part=domain_part)
    if not check_mx:
        return True
    return mx_check(
        email_address=email_address, from_address=from_address,
        helo_host=helo_host, smtp_timeout=smtp_timeout,
        dns_timeout=dns_timeout)


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
