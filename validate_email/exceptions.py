from collections import namedtuple
from typing import Dict

SMTPMessage = namedtuple(
    typename='SmtpMessage',
    field_names=['command', 'code', 'text', 'exceptions'])


class Error(Exception):
    'Base class for all exceptions of this module.'
    message = 'Unknown error.'

    def __str__(self):
        return self.message


class ParameterError(Error):
    """
    Base class for all exceptions indicating a wrong function parameter.
    """


class FromAddressFormatError(ParameterError):
    """
    Raised when the from email address used for the MX check has an
    invalid format.
    """
    message = 'Invalid "From:" email address.'


class EmailValidationError(Error):
    'Base class for all exceptions indicating validation failure.'


class AddressFormatError(EmailValidationError):
    'Raised when the email address has an invalid format.'
    message = 'Invalid email address.'


class DomainBlacklistedError(EmailValidationError):
    """
    Raised when the domain of the email address is blacklisted on
    https://github.com/disposable-email-domains/disposable-email-domains.
    """
    message = 'Domain blacklisted.'


class DNSError(EmailValidationError):
    """
    Base class of all exceptions that indicate failure to determine a
    valid MX for the domain of email address.
    """


class DomainNotFoundError(DNSError):
    'Raised when the domain is not found.'
    message = 'Domain not found.'


class NoNameserverError(DNSError):
    'Raised when the domain does not resolve by nameservers in time.'
    message = 'No nameserver found for domain.'


class DNSTimeoutError(DNSError):
    'Raised when the domain lookup times out.'
    message = 'Domain lookup timed out.'


class DNSConfigurationError(DNSError):
    """
    Raised when the DNS entries for this domain are falsely configured.
    """
    message = 'Misconfigurated DNS entries for domain.'


class NoMXError(DNSError):
    'Raised when the domain has no MX records configured.'
    message = 'No MX record for domain found.'


class NoValidMXError(DNSError):
    """
    Raised when the domain has MX records configured, but none of them
    has a valid format.
    """
    message = 'No valid MX record for domain found.'


class SMTPError(EmailValidationError):
    """
    Base class for exceptions raised in the end from unsuccessful SMTP
    communication.

    `error_messages` is a dictionary with a `SMTPMessage` per MX record,
    where the hostname is the key and a tuple of command, error code,
    and error message is the value.
    """

    def __init__(self, error_messages: Dict[str, SMTPMessage]):
        self.error_messages = error_messages

    def __str__(self) -> str:
        return '\n'.join([self.message] + [
            f'{host}: {message.code} {message.text} '
            f'(in reply to {message.command!r})'
            for host, message in self.error_messages.items()
        ])


class AddressNotDeliverableError(SMTPError):
    """
    Raised when at least one of the MX sends an SMTP reply which
    unambiguously indicate an invalid (nonexistant, blocked, expired...)
    recipient email address.

    This exception indicates that the email address is clearly invalid.
    """
    message = 'Email address undeliverable:'


class SMTPCommunicationError(SMTPError):
    """
    Raised when the SMTP communication with all MX was unsuccessful for
    other reasons than an invalid recipient email address.

    This exception indicates a configuration issue either on the host
    where this program runs or on the MX. A possible reason is that the
    local host ist blacklisted on the MX.
    """
    message = 'SMTP communication failure:'


class SMTPTemporaryError(SMTPError):
    """
    Raised when the email address cannot be verified because none of the
    MX gave a clear "yes" or "no" about the existence of the address,
    but at least one gave a temporary error reply to the "RCPT TO:"
    command.

    This exception indicates that the validity of the email address
    cannot be verified, either for reasons of MX configuration (like
    greylisting) or due to temporary server issues on the MX.
    """
    message = 'Temporary error in email address verification:'


class TLSNegotiationError(EmailValidationError):
    'Raised when an error happens during the TLS negotiation.'
    _str = 'During TLS negotiation, the following exception(s) happened: {exc}'

    def __str__(self):
        'Print a readable depiction of what happened.'
        return self._str.format(exc=', '.join(repr(x) for x in self.args))
