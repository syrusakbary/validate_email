from logging import getLogger
from smtplib import SMTP, SMTPNotSupportedError, SMTPServerDisconnected
from socket import error as SocketError
from socket import gethostname
from typing import Optional

from dns.exception import Timeout
from dns.rdatatype import MX as rdtype_mx
from dns.rdtypes.ANY.MX import MX
from dns.resolver import (
    NXDOMAIN, YXDOMAIN, Answer, NoAnswer, NoNameservers, resolve)

from .constants import HOST_REGEX
from .email_address import EmailAddress
from .exceptions import (
    AddressNotDeliverableError, DNSConfigurationError, DNSTimeoutError,
    DomainNotFoundError, NoMXError, NoNameserverError, NoValidMXError)

LOGGER = getLogger(name=__name__)


class _ProtocolError(Exception):
    """
    Raised when there is an error during the SMTP conversation.
    Used only internally.
    """

    def __init__(self, command: str, code: int, message: bytes):
        self.command = command
        self.code = code
        self.message = message.decode(errors='ignore')

    def __str__(self):
        return f'{self.code} {self.message} (in reply to {self.command})'


def _get_mx_records(domain: str, timeout: int) -> list:
    'Return the DNS response for checking, optionally raise exceptions.'
    try:
        return resolve(
            qname=domain, rdtype=rdtype_mx, lifetime=timeout,
            search=True)  # type: Answer
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


def _get_cleaned_mx_records(domain: str, timeout: int) -> list:
    """
    Return a list of hostnames in the MX record, raise an exception on
    any issues.
    """
    records = _get_mx_records(domain=domain, timeout=timeout)
    to_check = list()
    host_set = set()
    for record in records:  # type: MX
        dns_str = record.exchange.to_text().rstrip('.')  # type: str
        if dns_str in host_set:
            continue
        to_check.append(dns_str)
        host_set.add(dns_str)
    result = [x for x in to_check if HOST_REGEX.search(string=x)]
    if not result:
        raise NoValidMXError
    return result


def _smtp_ehlo_tls(smtp: SMTP, helo_host: str):
    """
    Try and start the TLS session, fall back to unencrypted when
    unavailable.
    """
    code, message = smtp.ehlo(name=helo_host)
    if code >= 300:
        # EHLO bails out, no further SMTP commands are acceptable
        raise _ProtocolError('EHLO', code, message)
    try:
        smtp.starttls()
        code, message = smtp.ehlo(name=helo_host)
    except SMTPNotSupportedError:
        # The server does not support the STARTTLS extension
        pass
    except RuntimeError:
        # SSL/TLS support is not available to your Python interpreter
        pass


def _smtp_mail(smtp: SMTP, from_address: EmailAddress):
    'Send and evaluate the `MAIL FROM` command.'
    code, message = smtp.mail(sender=from_address.ace)
    if code >= 300:
        # MAIL FROM bails out, no further SMTP commands are acceptable
        raise _ProtocolError('MAIL FROM', code, message)


def _smtp_converse(
        mx_record: str, smtp_timeout: int, debug: bool, helo_host: str,
        from_address: EmailAddress, email_address: EmailAddress):
    """
    Do the `SMTP` conversation, handle errors in the caller.

    Raise `_ProtocolError` on error, and `StopIteration` if the
    conversation points out an existing email.
    """
    if debug:
        LOGGER.debug(msg=f'Trying {mx_record} ...')
    with SMTP(timeout=smtp_timeout) as smtp:
        smtp._host = mx_record  # Workaround for bug in smtplib
        smtp.set_debuglevel(debuglevel=2 if debug else False)
        code, message = smtp.connect(host=mx_record)
        if code >= 400:
            raise _ProtocolError('connect', code, message)
        _smtp_ehlo_tls(smtp=smtp, helo_host=helo_host)
        _smtp_mail(smtp=smtp, from_address=from_address)
        code, message = smtp.rcpt(recip=email_address.ace)
        if code == 250:
            # Address valid, early exit
            raise StopIteration
        elif code >= 500:
            raise _ProtocolError('RCPT TO', code, message)


def _check_one_mx(
        error_messages: list, mx_record: str, helo_host: str,
        from_address: EmailAddress, email_address: EmailAddress,
        smtp_timeout: int, debug: bool) -> bool:
    """
    Check one MX server, return the `is_ambigious` boolean or raise
    `StopIteration` if this MX accepts the email.
    """
    try:
        _smtp_converse(
            mx_record=mx_record, smtp_timeout=smtp_timeout, debug=debug,
            helo_host=helo_host, from_address=from_address,
            email_address=email_address)
    except SMTPServerDisconnected:
        return True
    except (SocketError, _ProtocolError) as error:
        error_messages.append(f'{mx_record}: {error}')
        return False
    return True


def _check_mx_records(
        mx_records: list, smtp_timeout: int, helo_host: str,
        from_address: EmailAddress, email_address: EmailAddress,
        debug: bool) -> Optional[bool]:
    'Check the mx records for a given email address.'
    # TODO: Raise an ambigious exception, containing the messages? Will
    # be a breaking change.
    error_messages = []
    found_ambigious = False
    for mx_record in mx_records:
        try:
            found_ambigious |= _check_one_mx(
                error_messages=error_messages, mx_record=mx_record,
                helo_host=helo_host, from_address=from_address,
                email_address=email_address, smtp_timeout=smtp_timeout,
                debug=debug)
        except StopIteration:
            # Address valid, early exit
            return True
    # If any of the mx servers behaved ambigious, return None, otherwise raise
    # an exception containing the collected error messages.
    if not found_ambigious:
        raise AddressNotDeliverableError(error_messages=error_messages)


def mx_check(
    email_address: EmailAddress, debug: bool,
    from_address: Optional[EmailAddress] = None,
    helo_host: Optional[str] = None, smtp_timeout: int = 10,
    dns_timeout: int = 10, skip_smtp: bool = False
) -> Optional[bool]:
    """
    Return `True` if the host responds with a deliverable response code,
    `False` if not-deliverable. Also, return `None` if there if couldn't
    provide a conclusive result (e.g. temporary errors or graylisting).
    """
    host = helo_host or gethostname()
    from_address = from_address or email_address
    if email_address.domain_literal_ip:
        mx_records = [email_address.domain_literal_ip]
    else:
        mx_records = _get_cleaned_mx_records(
            domain=email_address.domain, timeout=dns_timeout)
    if skip_smtp:
        return True
    return _check_mx_records(
        mx_records=mx_records, smtp_timeout=smtp_timeout, helo_host=host,
        from_address=from_address, email_address=email_address, debug=debug)
