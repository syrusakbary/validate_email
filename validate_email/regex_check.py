from ipaddress import IPv4Address, IPv6Address
from typing import Optional

from .constants import HOST_REGEX, LITERAL_REGEX, USER_REGEX

SetOrNone = Optional[set]


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
    if _validate_ipv4_address(value):
        return True
    return _validate_ipv6_address(value)


class RegexValidator(object):
    'Slightly adjusted email regex checker from the Django project.'

    def __call__(
            self, user_part: str, domain_part: str,
            use_blacklist: bool = True) -> bool:
        if not USER_REGEX.match(user_part):
            return False

        if not self.validate_domain_part(domain_part):
            # Try for possible IDN domain-part
            try:
                domain_part = domain_part.encode('idna').decode('ascii')
            except UnicodeError:
                pass
            else:
                if self.validate_domain_part(domain_part):
                    return True
            return False
        return True

    def validate_domain_part(self, domain_part):
        if HOST_REGEX.match(domain_part):
            return True

        literal_match = LITERAL_REGEX.match(domain_part)
        if literal_match:
            ip_address = literal_match.group(1)
            return _validate_ipv46_address(ip_address)
        return False


regex_check = RegexValidator()
