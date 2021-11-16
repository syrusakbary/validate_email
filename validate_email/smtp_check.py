from logging import getLogger
from smtplib import (
    SMTP, SMTPNotSupportedError, SMTPResponseException, SMTPServerDisconnected)
from ssl import SSLContext, SSLError
from typing import List, Optional, Tuple

from .email_address import EmailAddress
from .exceptions import (
    AddressNotDeliverableError, SMTPCommunicationError, SMTPMessage,
    SMTPTemporaryError, TLSNegotiationError)

LOGGER = getLogger(name=__name__)


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
            self, local_hostname: Optional[str], timeout: float, debug: bool,
            sender: EmailAddress, recip: EmailAddress,
            skip_tls: bool = False, tls_context: SSLContext = None):
        """
        Initialize the object with all the parameters which remain
        constant during the check of one email address on all the SMTP
        servers.
        """
        super().__init__(local_hostname=local_hostname, timeout=timeout)
        self.set_debuglevel(debuglevel=2 if debug else False)
        self.__sender = sender
        self.__recip = recip
        self.__temporary_errors = {}
        self.__skip_tls = skip_tls
        self.__tls_context = tls_context
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
        # Use an OS assigned source port if source_address is passed
        _source_address = None if source_address is None \
            else (source_address, 0)
        try:
            code, message = super().connect(
                host=host, port=port, source_address=_source_address)
        except OSError as error:
            raise SMTPServerDisconnected(str(error))
        if code >= 400:
            raise SMTPResponseException(code=code, msg=message)
        return code, message.decode()

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
        except SSLError as exc:
            raise TLSNegotiationError(exc)

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
                    text=message.decode(errors='ignore'), exceptions=())})
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

    def _handle_smtpresponseexception(
            self, exc: SMTPResponseException) -> bool:
        'Handle an `SMTPResponseException`.'
        smtp_error = exc.smtp_error.decode(errors='ignore') \
            if type(exc.smtp_error) is bytes else exc.smtp_error
        smtp_message = SMTPMessage(
            command=self.__command, code=exc.smtp_code,
            text=smtp_error, exceptions=(exc,))
        if exc.smtp_code >= 500:
            raise SMTPCommunicationError(
                error_messages={self._host: smtp_message})
        else:
            self.__temporary_errors[self._host] = smtp_message
        return False

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
            if not self.__skip_tls:
                self.starttls(context=self.__tls_context)
            self.ehlo_or_helo_if_needed()
            self.mail(sender=self.__sender.ace)
            code, _ = self.rcpt(recip=self.__recip.ace)
        except SMTPServerDisconnected as exc:
            self.__temporary_errors[self._host] = SMTPMessage(
                command=self.__command, code=451, text=str(exc),
                exceptions=(exc,))
            return False
        except SMTPResponseException as exc:
            return self._handle_smtpresponseexception(exc=exc)
        except TLSNegotiationError as exc:
            self.__temporary_errors[self._host] = SMTPMessage(
                command=self.__command, code=-1, text=str(exc),
                exceptions=exc.args)
            return False
        finally:
            self.quit()
        return code < 400

    def check(self, hosts: List[str]) -> bool:
        """
        Run the check for all given SMTP servers. On positive result,
        return `True`, else raise exceptions described in `smtp_check`.
        """
        for host in hosts:
            LOGGER.debug(msg=f'Trying {host} ...')
            if self._check_one(host=host):
                return True
        # Raise exception for collected temporary errors
        if self.__temporary_errors:
            raise SMTPTemporaryError(error_messages=self.__temporary_errors)
        return False


def smtp_check(
    email_address: EmailAddress, mx_records: List[str], timeout: float = 10,
    helo_host: Optional[str] = None,
    from_address: Optional[EmailAddress] = None,
    skip_tls: bool = False, tls_context: Optional[SSLContext] = None,
    debug: bool = False
) -> bool:
    """
    Returns `True` as soon as the any of the given server accepts the
    recipient address.

    Raise an `AddressNotDeliverableError` if any server unambiguously
    and permanently refuses to accept the recipient address.

    Raise `SMTPTemporaryError` if all the servers answer with a
    temporary error code during the SMTP communication. This means that
    the validity of the email address can not be determined. Greylisting
    or server delivery issues can be a cause for this.

    Raise `SMTPCommunicationError` if any SMTP server replies with an
    error message to any of the communication steps before the recipient
    address is checked, and the validity of the email address can not be
    determined either.
    """
    smtp_checker = _SMTPChecker(
        local_hostname=helo_host, timeout=timeout, debug=debug,
        sender=from_address or email_address, recip=email_address,
        skip_tls=skip_tls, tls_context=tls_context)
    return smtp_checker.check(hosts=mx_records)
