from ipaddress import IPv4Address, IPv6Address

from .constants import HOST_REGEX, LITERAL_REGEX, USER_REGEX
from .email_address import EmailAddress
from .exceptions import AddressFormatError


def _validate_ipv4_address(value: str):
    try:
        IPv4Address(address=value)
    except ValueError:
        return False
    return True


def _validate_ipv6_address(value: str) -> bool:
    """
    Return whether or not the `ip_str` string is a valid IPv6 address.
    """
    try:
        IPv6Address(address=value)
    except ValueError:
        return False
    return True


def _validate_ipv46_address(value: str) -> bool:
    return _validate_ipv4_address(value) or _validate_ipv6_address(value)


def regex_check(address: EmailAddress) -> bool:
    'Slightly adjusted email regex checker from the Django project.'

    # Validate user part.
    if not USER_REGEX.match(address.user):
        raise AddressFormatError

    # Validate domain part: a) hostname.
    if HOST_REGEX.match(address.ace_domain):
        return True

    # Validate domain part: b) literal IP address.
    literal_match = LITERAL_REGEX.match(address.ace_domain)
    if literal_match:
        ip_address = literal_match.group(1)
        if _validate_ipv46_address(ip_address):
            return True

    # Domain part not successfully validated.
    raise AddressFormatError
