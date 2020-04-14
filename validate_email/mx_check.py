from smtplib import SMTP, SMTPServerDisconnected
from socket import error as SocketError
from socket import gethostname
from typing import Optional

from dns.exception import Timeout
from dns.rdatatype import MX as rdtype_mx
from dns.rdtypes.ANY.MX import MX
from dns.resolver import (
    NXDOMAIN, YXDOMAIN, Answer, NoAnswer, NoNameservers, query)

from .constants import HOST_REGEX
from .email_address import EmailAddress
from .exceptions import (
    AddressNotDeliverableError, DNSConfigurationError, DNSTimeoutError,
    DomainNotFoundError, NoMXError, NoNameserverError, NoValidMXError)


def _get_mx_records(domain: str, timeout: int) -> list:
    """
    Return a list of hostnames in the MX record, raise an exception on
    any issues.
    """
    try:
        records = query(
            qname=domain, rdtype=rdtype_mx, lifetime=timeout)  # type: Answer
    except NXDOMAIN:
        raise DomainNotFoundError
    except NoNameservers:
        raise NoNameserverError
    except Timeout:
        raise DNSTimeoutError
    except YXDOMAIN:
        raise DNSConfigurationError
    except NoAnswer:
        raise NoMXError
    to_check = dict()
    for record in records:  # type: MX
        dns_str = record.exchange.to_text()  # type: str
        to_check[dns_str] = dns_str[:-1] if dns_str.endswith('.') else dns_str
    result = [k for k, v in to_check.items() if HOST_REGEX.search(string=v)]
    if not result:
        raise NoValidMXError
    return result


def _check_one_mx(
        smtp: SMTP, error_messages: list, mx_record: str, helo_host: str,
        from_address: EmailAddress, email_address: EmailAddress) -> bool:
    """
    Check one MX server, return the `is_ambigious` boolean or raise
    `StopIteration` if this MX accepts the email.
    """
    try:
        smtp.connect(host=mx_record)
        smtp.helo(name=helo_host)
        smtp.mail(sender=from_address.ace)
        code, message = smtp.rcpt(recip=email_address.ace)
        smtp.quit()
    except SMTPServerDisconnected:
        return True
    except SocketError as error:
        error_messages.append(f'{mx_record}: {error}')
        return False
    if code == 250:
        raise StopIteration
    elif 400 <= code <= 499:
        # Ambigious return code, can be graylist, temporary problems,
        # quota or mailsystem error
        return True
    message = message.decode(errors='ignore')
    error_messages.append(f'{mx_record}: {code} {message}')
    return False


def _check_mx_records(
    mx_records: list, smtp_timeout: int, helo_host: str,
    from_address: EmailAddress, email_address: EmailAddress
) -> Optional[bool]:
    'Check the mx records for a given email address.'
    smtp = SMTP(timeout=smtp_timeout)
    smtp.set_debuglevel(debuglevel=0)
    error_messages = []
    found_ambigious = False
    for mx_record in mx_records:
        try:
            found_ambigious |= _check_one_mx(
                smtp=smtp, error_messages=error_messages, mx_record=mx_record,
                helo_host=helo_host, from_address=from_address,
                email_address=email_address)
        except StopIteration:
            return True
    # If any of the mx servers behaved ambigious, return None, otherwise raise
    # an exception containing the collected error messages.
    if not found_ambigious:
        raise AddressNotDeliverableError(error_messages)


def mx_check(
    email_address: EmailAddress, from_address: Optional[EmailAddress] = None,
    helo_host: Optional[str] = None, smtp_timeout: int = 10,
    dns_timeout: int = 10
) -> Optional[bool]:
    """
    Return `True` if the host responds with a deliverable response code,
    `False` if not-deliverable.
    Also, return `None` if there if couldn't provide a conclusive result
    (e.g. temporary errors or graylisting).
    """
    host = helo_host or gethostname()
    from_address = from_address or email_address
    if email_address.domain_literal_ip:
        mx_records = [email_address.domain_literal_ip]
    else:
        mx_records = _get_mx_records(
            domain=email_address.domain, timeout=dns_timeout)
    return _check_mx_records(
        mx_records=mx_records, smtp_timeout=smtp_timeout, helo_host=host,
        from_address=from_address, email_address=email_address)
