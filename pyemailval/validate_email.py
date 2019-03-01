from .regex_check import regex_check
from .mx_check import mx_check


def validate_email(
        email_address, check_regex=True, check_mx=True, smtp_timeout=10):

    if check_regex and not regex_check(email_address):
        return False

    if check_mx and not mx_check(email_address, smtp_timeout=smtp_timeout):
        return False

    return True
