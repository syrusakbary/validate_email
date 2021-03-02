from logging import getLogger
from smtplib import (
    SMTP, SMTPNotSupportedError, SMTPResponseException, SMTPServerDisconnected)
from typing import List, Optional, Tuple

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
    SMTPCommunicationError, SMTPMessage, SMTPTemporaryError)

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
            sender: EmailAddress, recip: EmailAddress):
        """
        Initialize the object with all the parameters which remain
        constant during the check of one email address on all the SMTP
        servers.
        """
        super().__init__(local_hostname=local_hostname, timeout=timeout)
        self.set_debuglevel(debuglevel=2 if debug else False)
        self.__sender = sender
        self.__recip = recip
        self.__communication_errors = {}
        self.__temporary_errors = {}
        # Avoid error on close() after unsuccessful connect
        self.sock = None

    def putcmd(self, cmd: str, args: str = ''):
        """
        Like `smtplib.SMTP.putcmd`, but remember the command for later
        use in error messages.
        """
        if args:
            self.__command = f'{cmd} {args}'
        else:
            self.__command = cmd
        super().putcmd(cmd=cmd, args=args)

    def connect(
            self, host: str = 'localhost', port: int = 0,
            source_address: str = None) -> Tuple[int, str]:
        """
        Like `smtplib.SMTP.connect`, but raise appropriate exceptions on
        connection failure or negative SMTP server response.
        """
        self.__command = 'connect'  # Used for error messages.
        self._host = host  # Workaround: Missing in standard smtplib!
        try:
            code, message = super().connect(
                host=host, port=port, source_address=source_address)
        except OSError as error:
            raise SMTPServerDisconnected(str(error))
        if code >= 400:
            raise SMTPResponseException(code=code, msg=message)
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

    def mail(self, sender: str, options: tuple = ()):
        """
        Like `smtplib.SMTP.mail`, but raise an appropriate exception on
        negative SMTP server response.
        A code > 400 is an error here.
        """
        code, message = super().mail(sender=sender, options=options)
        if code >= 400:
            raise SMTPResponseException(code=code, msg=message)
        return code, message

    def rcpt(self, recip: str, options: tuple = ()):
        """
        Like `smtplib.SMTP.rcpt`, but handle negative SMTP server
        responses directly.
        """
        code, message = super().rcpt(recip=recip, options=options)
        if code >= 500:
            # Address clearly invalid: issue negative result
            raise AddressNotDeliverableError({
                self._host: SMTPMessage(
                    command='RCPT TO', code=code,
                    text=message.decode(errors='ignore'))})
        elif code >= 400:
            raise SMTPResponseException(code=code, msg=message)
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
        Run the check for one SMTP server.

        Return `True` on positive result.

        Return `False` on ambiguous result (4xx response to `RCPT TO`),
        while collecting the error message for later use.

        Raise `AddressNotDeliverableError`. on negative result.
        """
        try:
            self.connect(host=host)
            self.starttls()
            self.ehlo_or_helo_if_needed()
            self.mail(sender=self.__sender.ace)
            code, message = self.rcpt(recip=self.__recip.ace)
        except SMTPServerDisconnected as e:
            self.__communication_errors[self._host] = SMTPMessage(
                command=self.__command, code=0, text=str(e))
            return False
        except SMTPResponseException as e:
            smtp_message = SMTPMessage(
                command=self.__command, code=e.smtp_code,
                text=e.smtp_error.decode(errors='ignore'))
            if e.smtp_code >= 500:
                self.__communication_errors[self._host] = smtp_message
            else:
                self.__temporary_errors[self._host] = smtp_message
            return False
        finally:
            self.quit()
        return code < 400

    def check(self, hosts: List[str]) -> bool:
        """
        Run the check for all given SMTP servers. On positive result,
        return `True`, else raise exceptions described in `mx_check`.
        """
        for host in hosts:
            LOGGER.debug(msg=f'Trying {host} ...')
            if self._check_one(host=host):
                return True
        # Raise appropriate exceptions when necessary
        if self.__communication_errors:
            raise SMTPCommunicationError(
                error_messages=self.__communication_errors)
        elif self.__temporary_errors:
            raise SMTPTemporaryError(error_messages=self.__temporary_errors)


def mx_check(
        email_address: EmailAddress, debug: bool,
        from_address: Optional[EmailAddress] = None,
        helo_host: Optional[str] = None, smtp_timeout: int = 10,
        dns_timeout: int = 10, skip_smtp: bool = False) -> bool:
    """
    Returns `True` as soon as the any server accepts the recipient
    address.

    Raise an `AddressNotDeliverableError` if any server unambiguously
    and permanently refuses to accept the recipient address.

    Raise `SMTPTemporaryError` if the server answers with a temporary
    error code when validity of the email address can not be
    determined. Greylisting or server delivery issues can be a cause for
    this.

    Raise `SMTPCommunicationError` if the SMTP server(s) reply with an
    error message to any of the communication steps before the recipient
    address is checked, and the validity of the email address can not be
    determined either.

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
        sender=from_address, recip=email_address)
    return smtp_checker.check(hosts=mx_records)
