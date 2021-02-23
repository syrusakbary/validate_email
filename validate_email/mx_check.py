from logging import getLogger
from smtplib import (
    SMTP, SMTPNotSupportedError, SMTPResponseException, SMTPServerDisconnected)
from typing import List, Optional

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


class _SMTPChecker(SMTP):
    """
    A specialized variant of `smtplib.SMTP` for checking the validity of
    email addresses.

    All the commands used in the check process are modified to raise
    appropriate exceptions: `SMTPServerDisconnected` on connection
    issues and `SMTPResponseException` on negative SMTP server
    responses. Note that the methods of `smtplib.SMTP` already raise
    these exceptions on some conditions.

    Also, a new method `check` is added to run the check for a given
    list of SMTP servers.
    """
    def __init__(
            self, local_hostname: str, timeout: float, debug: bool,
            raise_communication_errors: bool,
            raise_temporary_errors: bool,
            sender: str, recip: str):
        """
        Initialize the object with all the parameters which remain
        constant during the check of one email address on all the SMTP
        servers.
        """
        super().__init__(local_hostname=local_hostname, timeout=timeout)
        self.set_debuglevel(debuglevel=2 if debug else False)
        self.__raise_communication_errors = raise_communication_errors
        self.__raise_temporary_errors = raise_temporary_errors
        self.__sender = sender
        self.__recip = recip
        self.__communication_errors = {}
        self.__temporary_errors = {}
        # Avoid error on close() after unsuccessful connect
        self.sock = None

    def putcmd(self, cmd, args=""):
        """
        Like `smtplib.SMTP.putcmd`, but remember the command for later
        use in error messages.
        """
        if args:
            self.__command = f'{cmd} {args}'
        else:
            self.__command = cmd
        super().putcmd(cmd, args)

    def connect(self, host, *args, **kwargs):
        """
        Like `smtplib.SMTP.connect`, but raise appropriate exceptions on
        connection failure or negative SMTP server response.
        """
        self.__command = 'connect'  # Used for error messages.
        self._host = host           # Missing in standard smtplib!
        try:
            code, message = super().connect(host, *args, **kwargs)
        except OSError as error:
            raise SMTPServerDisconnected(str(error))
        if code >= 400:
            raise SMTPResponseException(code, message)
        return code, message

    def starttls(self, *args, **kwargs):
        """
        Like `smtplib.SMTP.starttls`, but continue without TLS in case
        either end of the connection does not support it.
        """
        try:
            super().starttls(*args, **kwargs)
        except SMTPNotSupportedError:
            # The server does not support the STARTTLS extension
            pass
        except RuntimeError:
            # SSL/TLS support is not available to your Python interpreter
            pass

    def mail(self, *args, **kwargs):
        """
        Like `smtplib.SMTP.mail`, but raise an appropriate exception on
        negative SMTP server response.
        """
        code, message = super().mail(*args, **kwargs)
        if code >= 400:
            raise SMTPResponseException(code, message)
        return code, message

    def rcpt(self, *args, **kwargs):
        """
        Like `smtplib.SMTP.rcpt`, but handle negative SMTP server
        responses directly.
        """
        code, message = super().rcpt(*args, **kwargs)
        if code >= 500:
            # Address clearly invalid: issue negative result
            raise AddressNotDeliverableError({self._host: (
                    'RCPT TO', code, message.decode(errors='ignore'))})
        elif code >= 400:
            # Temporary error on this host: collect message
            self.__temporary_errors[self._host] = (
                    'RCPT TO', code, message.decode(errors='ignore'))
        return code, message

    def quit(self):
        """
        Like `smtplib.SMTP.quit`, but make sure that everything is
        cleaned up properly even if the connection has been lost before.
        """
        try:
            return super().quit()
        except SMTPServerDisconnected:
            self.ehlo_resp = self.helo_resp = None
            self.esmtp_features = {}
            self.does_esmtp = False
            self.close()

    def _check_one(self, host: str) -> bool:
        """
        Run the check for one SMTP server. On positive result, return
        `True`. On negative result, raise `AddressNotDeliverableError`.
        On ambiguous result (4xx response to `RCPT TO`) or any
        communication issue before even reaching `RCPT TO` in the
        protocol, collect error message for later use and return
        `False`.
        """
        try:
            self.connect(host)
            self.starttls()
            self.ehlo_or_helo_if_needed()
            self.mail(self.__sender)
            code, message = self.rcpt(self.__recip)
        except SMTPServerDisconnected as e:
            self.__communication_errors[self._host] = (
                    self.__command, 0, str(e))
            return False
        except SMTPResponseException as e:
            self.__communication_errors[self._host] = (
                    self.__command, e.smtp_code,
                    e.smtp_error.decode(errors='ignore'))
            return False
        finally:
            self.quit()
        return (code < 400)

    def check(self, hosts: List[str]) -> Optional[bool]:
        """
        Run the check for all given SMTP servers. On positive result,
        return `True`. On negative result, raise
        `AddressNotDeliverableError`. On ambiguous result (4xx
        response(s) to `RCPT TO`) or any communication issue(s) before
        even reaching `RCPT TO` in the protocol, either raise an
        exception or return `None` depending on the parameters.
        """
        for host in hosts:
            if self.debuglevel > 0:
                LOGGER.debug(msg=f'Trying {host} ...')
            if self._check_one(host):
                return True
        # Raise exceptions on ambiguous results if desired. If in doubt, raise
        # the CommunicationError because that one might point to local
        # configuration or blacklisting issues.
        if self.__communication_errors and self.__raise_communication_errors:
            raise SMTPCommunicationError(self.__communication_errors)
        if self.__temporary_errors and self.__raise_temporary_errors:
            raise SMTPTemporaryError(self.__temporary_errors)
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
    from_address = from_address or email_address
    if email_address.domain_literal_ip:
        mx_records = [email_address.domain_literal_ip]
    else:
        mx_records = _get_cleaned_mx_records(
            domain=email_address.domain, timeout=dns_timeout)
    if skip_smtp:
        return True
    smtp_checker = _SMTPChecker(
            local_hostname=helo_host, timeout=smtp_timeout, debug=debug,
            raise_communication_errors=raise_communication_errors,
            raise_temporary_errors=raise_temporary_errors,
            sender=from_address.ace, recip=email_address.ace)
    return smtp_checker.check(mx_records)
