class EmailValidationError(Exception):
    """
    Base class for all exceptions indicating validation failure.
    """
    message = 'Unknown error.'

    def __str__(self):
        return self.message


class AddressFormatError(EmailValidationError):
    """
    Raised when the email address has an invalid format.
    """
    message = 'Invalid email address.'


class DomainBlacklistedError(EmailValidationError):
    """
    Raised when the domain of the email address is blacklisted on
    https://git.com/martenson/disposable-email-domains.
    """
    message = 'Domain blacklisted.'


class DomainNotFoundError(EmailValidationError):
    """
    Raised when the domain of the email address is blacklisted on
    https://git.com/martenson/disposable-email-domains.
    """
    message = 'Domain not found.'


class NoNameserverError(EmailValidationError):
    """
    Raised when the domain of the email address is blacklisted on
    https://git.com/martenson/disposable-email-domains.
    """
    message = 'No nameserver found for domain.'


class DNSTimeoutError(EmailValidationError):
    """
    Raised when the domain of the email address is blacklisted on
    https://git.com/martenson/disposable-email-domains.
    """
    message = 'Domain lookup timed out.'


class DNSConfigurationError(EmailValidationError):
    """
    Raised when the domain of the email address is blacklisted on
    https://git.com/martenson/disposable-email-domains.
    """
    message = 'Misconfigurated DNS entries for domain.'


class NoMXError(EmailValidationError):
    """
    Raised when the domain of the email address is blacklisted on
    https://git.com/martenson/disposable-email-domains.
    """
    message = 'No MX record for domain found.'


class NoValidMXError(EmailValidationError):
    """
    Raised when the domain of the email address is blacklisted on
    https://git.com/martenson/disposable-email-domains.
    """
    message = 'No valid MX record for domain found.'


class AddressNotDeliverableError(EmailValidationError):
    """
    Raised when the domain of the email address is blacklisted on
    https://git.com/martenson/disposable-email-domains.
    """
    message = 'Non-deliverable email address:'

    def __init__(self, error_messages):
        self.message = '\n'.join([self.message] + error_messages)
