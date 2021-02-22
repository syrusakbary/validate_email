from logging import getLogger
from smtplib import SMTP, SMTPNotSupportedError, SMTPServerDisconnected
from socket import error as SocketError
from socket import gethostname
from typing import Optional, Tuple

from dns.exception import Timeout
from dns.rdatatype import MX as rdtype_mx
from dns.rdtypes.ANY.MX import MX
from dns.resolver import (
    NXDOMAIN, YXDOMAIN, Answer, NoAnswer, NoNameservers, resolve)

from .constants import HOST_REGEX
from .email_address import EmailAddress
from .exceptions import (
    AddressNotDeliverableError, DNSConfigurationError, DNSTimeoutError,
    DomainNotFoundError, NoMXError, NoNameserverError, NoValidMXError,
    SMTPCommunicationError, SMTPTemporaryError)

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
    if code >= 400:
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
    if code >= 400:
        # MAIL FROM bails out, no further SMTP commands are acceptable
        raise _ProtocolError('MAIL FROM', code, message)


def _smtp_converse(
        mx_record: str, smtp_timeout: int, debug: bool, helo_host: str,
        from_address: EmailAddress, email_address: EmailAddress
        ) -> Tuple[int, str]:
    """
    Do the `SMTP` conversation with one MX, and return code and message
    of the reply to the `RCPT TO:` command.

    If the conversation fails before the `RCPT TO:` command can be
    issued, a `_ProtocolError` is raised.
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
        return smtp.rcpt(recip=email_address.ace)


def _check_mx_records(
        mx_records: list, smtp_timeout: int, helo_host: str,
        from_address: EmailAddress, email_address: EmailAddress,
        debug: bool, raise_communication_errors: bool,
        raise_temporary_errors: bool) -> Optional[bool]:
    'Check the mx records for a given email address.'
    communication_errors = {}
    temporary_errors = {}
    for mx_record in mx_records:
        try:
            code, message = _smtp_converse(
                mx_record=mx_record, smtp_timeout=smtp_timeout, debug=debug,
                helo_host=helo_host, from_address=from_address,
                email_address=email_address)
            if code >= 500:
                # Address clearly invalid: exit early.
                raise AddressNotDeliverableError({mx_record: (
                        'RCPT TO', code, message.decode(errors='ignore'))})
            elif code >= 400:
                # Temporary error on this MX: collect message and continue.
                temporary_errors[mx_record] = (
                        'RCPT TO', code, message.decode(errors='ignore'))
            else:
                # Address clearly valid: exit early.
                return True
        except (SocketError, SMTPServerDisconnected) as error:
            # Connection problem: collect message and continue.
            communication_errors[mx_record] = ('connect', 0, error)
        except _ProtocolError as error:
            # SMTP communication error: collect message and continue.
            communication_errors[mx_record] = (
                    error.command, error.code, error.message)
    # Raise exceptions on ambiguous results if desired. If in doubt, raise the
    # CommunicationError because that one might point to local configuration or
    # blacklisting issues.
    if communication_errors and raise_communication_errors:
        raise SMTPCommunicationError(communication_errors)
    if temporary_errors and raise_temporary_errors:
        raise SMTPTemporaryError(temporary_errors)
    # Can't verify whether or not email address exists.
    return None


def mx_check(
        email_address: EmailAddress, debug: bool,
        from_address: Optional[EmailAddress] = None,
        helo_host: Optional[str] = None, smtp_timeout: int = 10,
        dns_timeout: int = 10, skip_smtp: bool = False,
        raise_communication_errors: bool = False,
        raise_temporary_errors: bool = False
        ) -> Optional[bool]:
    """
    Verify the given email address by determining the SMTP servers
    responsible for the domain and then asking them to deliver an
    email to the address. Before the actual message is sent, the
    process is interrupted.

    Returns `True` as soon as the any server accepts the recipient
    address.

    Raises a `AddressNotDeliverableError` if any server unambiguously
    and permanently refuses to accept the recipient address.

    If the server answers with a temporary error code, the validity of
    the email address can not be determined. In that case, the function
    returns `None`, or an `SMTPTemporaryError` is raised, dependent on
    the value of `raise_temporary_errors`. Greylisting is a frequent
    cause of this.

    If the SMTP server(s) reply with an error message to any of the
    communication steps before the recipient address is checked, the
    validity of the email address can not be determined either. In that
    case, the function returns `None`, or an `SMTPCommunicationError` is
    raised, dependent on the value of `raise_communication_errors`.

    In case no responsible SMTP servers can be determined, a variety of
    exceptions is raised depending on the exact issue, all derived from
    `MXError`.
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
        from_address=from_address, email_address=email_address, debug=debug,
        raise_communication_errors=raise_communication_errors,
        raise_temporary_errors=raise_temporary_errors)
