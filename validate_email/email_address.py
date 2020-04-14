from typing import Optional

from idna.core import IDNAError, encode

from .exceptions import AddressFormatError


class EmailAddress(object):
    """
    Internally used class to hold an email address.

    This class featuers splitting the email address into user and domain
    part as well as converting internationalized domain name into the
    ASCII-compatible encoding (ACE) according to the IDNA standard.
    """

    def __init__(self, address: str):
        self._address = address

        # Split email address into user and domain part.
        try:
            self._user, self._domain = self._address.rsplit('@', 1)
        except ValueError:
            raise AddressFormatError

        # Convert internationalized domain name into the ACE encoding
        if self.domain_literal_ip:
            self._ace_domain = self._domain
        else:
            try:
                self._ace_domain = encode(self._domain).decode('ascii')
            except IDNAError:
                raise AddressFormatError

    @property
    def user(self) -> str:
        """
        The username part of the email address, that is the part before
        the "@" sign.
        """
        return self._user

    @property
    def domain(self) -> str:
        """
        The domain part of the email address, that is the part after the
        "@" sign.
        """
        return self._domain

    @property
    def domain_literal_ip(self) -> Optional[str]:
        """
        If the domain part of the email address is a literal IP address
        enclosed in brackets, that IP address (without the brackets) is
        returned. Otherwise, `None` is returned.
        """
        if self._domain.startswith('[') and self._domain.endswith(']'):
            return self._domain[1:-1]

    @property
    def ace(self) -> str:
        'The ASCII-compatible encoding for the email address.'
        return '@'.join((self._user, self._ace_domain))

    @property
    def ace_domain(self) -> str:
        """
        The ASCII-compatible encoding for the domain part of the email
        address.
        """
        return self._ace_domain
