from ipaddress import IPv4Address, IPv6Address
from os.path import dirname, join
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


class EmailValidator(object):
    'Slightly adjusted email regex checker from the Django project.'
    domain_whitelist = frozenset('localhost')
    domain_blacklist = frozenset()

    def __init__(
            self, whitelist: SetOrNone = None, blacklist: SetOrNone = None):
        self.domain_whitelist = set(whitelist) \
            if whitelist else self.domain_whitelist
        self._load_blacklist(blacklist=blacklist)

    def _load_blacklist(self, blacklist: SetOrNone = None):
        'Load our blacklist.'
        self.domain_blacklist = set(blacklist) \
            if blacklist else self.domain_blacklist
        path = join(dirname(__file__), 'lib', 'blacklist.txt')
        try:
            with open(path) as fd:
                lines = fd.readlines()
        except FileNotFoundError:
            return
        self.domain_blacklist = self.domain_blacklist.union(
            x.strip() for x in lines)

    def __call__(self, value: str, use_blacklist: bool = True) -> bool:
        if not value or '@' not in value:
            return False

        user_part, domain_part = value.rsplit('@', 1)

        if not USER_REGEX.match(user_part):
            return False

        if domain_part in self.domain_whitelist:
            return True
        if domain_part in self.domain_blacklist:
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


regex_check = EmailValidator()
