from smtplib import SMTP, SMTPServerDisconnected
from socket import error as SocketError
from socket import gethostname
from typing import Optional

from dns.rdtypes.ANY.MX import MX
from dns.resolver import NXDOMAIN, Answer, NoAnswer, query

from .constants import EMAIL_EXTRACT_HOST_REGEX, HOST_REGEX


def _get_domain_from_email_address(email_address):
    try:
        return EMAIL_EXTRACT_HOST_REGEX.search(string=email_address)[1]
    except TypeError:
        raise ValueError('Invalid email address')
    except IndexError:
        raise ValueError('Invalid email address')


def _get_mx_records(domain: str) -> list:
    'Return a list of hostnames in the MX record.'
    try:
        records = query(domain, 'MX')  # type: Answer
    except NXDOMAIN:
        raise ValueError(f'Domain {domain} does not seem to exist')
    except NoAnswer:
        raise ValueError(f'Domain {domain} does not have an MX record')
    to_check = dict()
    for record in records:  # type: MX
        dns_str = record.exchange.to_text()  # type: str
        to_check[dns_str] = dns_str[:-1] if dns_str.endswith('.') else dns_str
    result = [k for k, v in to_check.items() if HOST_REGEX.search(string=v)]
    if not len(result):
        raise ValueError(f'Domain {domain} does not have a valid MX record')
    return result


def _check_mx_records(
    mx_records: list, smtp_timeout: int, helo_host: str, from_address: str,
    email_address: str
) -> Optional[bool]:
    'Check the mx records for a given email address.'
    smtp = SMTP(timeout=smtp_timeout)
    smtp.set_debuglevel(debuglevel=0)
    answers = set()
    for mx_record in mx_records:
        try:
            smtp.connect(host=mx_record)
            smtp.helo(name=helo_host)
            smtp.mail(sender=from_address)
            code, message = smtp.rcpt(recip=email_address)
            smtp.quit()
        except SMTPServerDisconnected:
            answers.add(None)
            continue
        except SocketError:
            answers.add(False)
            continue
        if code == 250:
            return True
        if 400 <= code <= 499:
            # Ambigious return code, can be graylist, temporary
            # problems, quota or mailsystem error
            answers.add(None)
    return None if None in answers else False


def mx_check(
    email_address: str, from_address: Optional[str] = None,
    helo_host: Optional[str] = None, smtp_timeout: int = 10
) -> Optional[bool]:
    """
    Return `True` if the host responds with a deliverable response code,
    `False` if not-deliverable.
    Also, return `None` if there if couldn't provide a conclusive result
    (e.g. temporary errors or graylisting).
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
