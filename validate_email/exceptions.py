from typing import Iterable


class EmailValidationError(Exception):
    'Base class for all exceptions indicating validation failure.'
    message = 'Unknown error.'

    def __str__(self):
        return self.message


class AddressFormatError(EmailValidationError):
    'Raised when the email address has an invalid format.'
    message = 'Invalid email address.'


class FromAddressFormatError(EmailValidationError):
    """
    Raised when the from email address used for the MX check has an
    invalid format.
    """
    message = 'Invalid "From:" email address.'


class DomainBlacklistedError(EmailValidationError):
    """
    Raised when the domain of the email address is blacklisted on
    https://github.com/martenson/disposable-email-domains.
    """
    message = 'Domain blacklisted.'


class DomainNotFoundError(EmailValidationError):
    'Raised when the domain is not found.'
    message = 'Domain not found.'


class NoNameserverError(EmailValidationError):
    'Raised when the domain does not resolve by nameservers in time.'
    message = 'No nameserver found for domain.'


class DNSTimeoutError(EmailValidationError):
    'Raised when the domain lookup times out.'
    message = 'Domain lookup timed out.'


class DNSConfigurationError(EmailValidationError):
    """
    Raised when the DNS entries for this domain are falsely configured.
    """
    message = 'Misconfigurated DNS entries for domain.'


class NoMXError(EmailValidationError):
    'Raised then the domain has no MX records configured.'
    message = 'No MX record for domain found.'


class NoValidMXError(EmailValidationError):
    message = 'No valid MX record for domain found.'


class AddressNotDeliverableError(EmailValidationError):
    'Raised when a non-ambigious resulted lookup fails.'
    message = 'Email address undeliverable:'

    def __init__(self, error_messages: Iterable):
        self.error_messages = error_messages

    def __str__(self) -> str:
        return '\n'.join([self.message] + self.error_messages)
