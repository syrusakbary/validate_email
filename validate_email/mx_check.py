from re import compile as re_compile
from smtplib import SMTP, SMTPServerDisconnected
from socket import error as SocketError
from socket import gethostname
from typing import Optional

from dns.resolver import NXDOMAIN, NoAnswer, query

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
        records = query(domain, 'MX')
    except NXDOMAIN:
        raise ValueError(f'Domain {domain} does not seem to exist')
    except NoAnswer:
        raise ValueError(f'Domain {domain} does not have an MX record')
    return [str(x.exchange) for x in records]


def _check_mx_records(
    mx_records: list, smtp_timeout: int, helo_host: str, from_address: str,
    email_address: str
) -> bool:
    'Check the mx records for a given email address.'
    smtp = SMTP(timeout=smtp_timeout)
    smtp.set_debuglevel(0)
    for mx_record in mx_records:
        try:
            smtp.connect(mx_record)
        except SocketError:
            continue
        smtp.helo(name=helo_host)
        smtp.mail(sender=from_address)
        code, message = smtp.rcpt(recip=email_address)
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
    domain = _get_domain_from_email_address(email_address)
    try:
        mx_records = _get_mx_records(domain)
    except ValueError:
        return False
    return _check_mx_records(
        mx_records=mx_records, smtp_timeout=smtp_timeout, helo_host=host,
        from_address=from_address, email_address=email_address)
