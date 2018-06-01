from regex_check import regex_check
from mx_check import mx_check


def validate_email(
        email_address,
        regex_check=True,
        mx_check=True,
        smtp_timeout=10):

    if regex_check and not regex_check(email_address):
        return False

    if mx_check and not mx_check(email_address, smtp_timeout=smtp_timeout):
        return False

    return True
