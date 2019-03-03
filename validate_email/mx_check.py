from re import compile as re_compile
from smtplib import SMTP, SMTPServerDisconnected
from socket import gethostname
from typing import Optional

import dns.resolver as dns

DOMAIN_REGEX = re_compile(r'(?<=@)\[?([^\[\]]+)')


def _get_domain_from_email_address(email_address):
    try:
        return DOMAIN_REGEX.search(string=email_address)[1]
    except TypeError:
        raise ValueError('Invalid email address')
    except IndexError:
        raise ValueError('Invalid email address')


def _get_mx_records(domain: str) -> list:
    try:
        records = dns.query(domain, 'MX')
    except dns.NXDOMAIN:
        raise ValueError(f'Domain {domain} does not seem to exist')
    return [str(x.exchange) for x in records]


def mx_check(
    email_address: str, from_address: Optional[str] = None,
    helo_host: Optional[str] = None, smtp_timeout: int = 10
) -> Optional[bool]:
    """
    Return `True` if the host responds with a deliverable response code,
    `False` if not-deliverable.
    Also, return `None` if there was an error.
    """
    from_address = from_address or email_address
    host = helo_host or gethostname()

    smtp = SMTP(timeout=smtp_timeout)
    smtp.set_debuglevel(0)

    domain = _get_domain_from_email_address(email_address)
    try:
        mx_records = _get_mx_records(domain)
    except ValueError:
        return False

    for mx_record in mx_records:
        smtp.connect(mx_record)
        smtp.helo(host)
        smtp.mail(from_address)
        code, message = smtp.rcpt(email_address)
        try:
            smtp.quit()
        except SMTPServerDisconnected:
            return None
        if code == 250:
            return True
        if 400 <= code <= 499:
            # Ambigious return code, can be graylist, or temporary
            # problems
            return None
    return False
