from re import compile as re_compile
from smtplib import SMTP
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


def _get_mx_records(domain):
    try:
        records = dns.query(domain, 'MX')
    except dns.NXDOMAIN:
        raise ValueError('Domain {} does not seem to exist')
    except Exception:
        raise NotImplementedError('Feature not yet implemented')
    return [str(x.exchange) for x in records]


def mx_check(
        email_address: str, from_address: Optional[str] = None,
        smtp_timeout: int = 10) -> bool:
    from_address = from_address or email_address
    host = gethostname()

    smtp = SMTP(timeout=smtp_timeout)
    smtp.set_debuglevel(0)

    domain = _get_domain_from_email_address(email_address)
    mx_records = _get_mx_records(domain)

    for mx_record in mx_records:
        smtp.connect(mx_record)
        smtp.helo(host)
        smtp.mail(from_address)
        code, message = smtp.rcpt(email_address)
        smtp.quit()
        return True
        if code == 250:
            return True
    return False
