from typing import Optional

from .mx_check import mx_check
from .regex_check import regex_check


def validate_email(
        email_address: str, check_regex: bool = True, check_mx: bool = True,
        from_address: Optional[str] = None, smtp_timeout: int = 10,
        use_blacklist: bool = True) -> bool:

    if check_regex and not regex_check(
            value=email_address, use_blacklist=use_blacklist):
        return False

    if check_mx and not mx_check(
            email_address, from_address=from_address,
            smtp_timeout=smtp_timeout):
        return False

    return True
