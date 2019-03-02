from typing import Optional

from .mx_check import mx_check
from .regex_check import regex_check


def validate_email(
        email_address: str, check_regex: bool = True, check_mx: bool = True,
        from_address: Optional[str] = None, helo_host: Optional[str] = None,
        smtp_timeout: int = 10, use_blacklist: bool = True) -> Optional[bool]:
    """
    Return `True` or `False` depending if the email address exists
    or/and can be delivered.

    Return `None` if the result is ambigious.
    """
    if check_regex and not regex_check(
            value=email_address, use_blacklist=use_blacklist):
        return False
    if not check_mx:
        return True
    return mx_check(
        email_address=email_address, from_address=from_address,
        helo_host=helo_host, smtp_timeout=smtp_timeout)
