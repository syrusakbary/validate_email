from unittest.case import TestCase

from validate_email.email_address import EmailAddress
from validate_email.exceptions import AddressFormatError
from validate_email.regex_check import regex_check

VALID_EXAMPLES = [
    'email@domain.com',  # basic valid email
    'firstname.lastname@domain.com',  # dot in address field
    'email@subdomain.domain.com',  # dot in subdomain
    'firstname+lastname@domain.com',  # + in address field
    'email@123.123.123.123',  # domain address is IP address
    'email@[123.123.123.123]',  # square brackets around IP address
    '\'email\'@domain.com',  # quote marks in address fields
    '1234567890@domain.com',  # numbers in address field
    'email@domain-one.com',  # dash in subdomain
    '_______@domain.com',  # underscore in address field
    'email@domain.name',  # .name top level domain name
    'email@domain.co.jp',  # dot in top level domain
    'firstname-lastname@domain.com'  # dash in address field
]

INVALID_EXAMPLES = [
    '#@%^%#$@#$@#.com',  # garbage
    '@domain.com',  # missing username
    'Joe Smith <email@domain.com>',  # encoded html within email is invalid
    'email@domain@domain.com',  # two @ sign
    '.email@domain.com',  # leading dot in address is not allowed
    'email.@domain.com',  # trailing dot in address is not allowed
    'email..email@domain.com',  # multiple dots
    'あいうえお@domain.com',  # unicode char as address
    'email@domain.com (Joe Smith)',  # text followed email is not allowed
    'email@domain',  # missing top level domain (.com/.net/.org/etc)
    'email@-domain.com',  # leading dash in front of domain is invalid
    'email@domain..com',  # multiple dot in the domain portion is invalid
]


class FormatValidity(TestCase):
    'Testing regex validation + format validity.'

    def test_valid_email_structure_regex(self):
        'Accepts an email with a valid structure.'
        for address in VALID_EXAMPLES:
            self.assertTrue(
                expr=regex_check(EmailAddress(address)),
                msg=f'Check is not true with {address}')

    def test_invalid_email_structure_regex(self):
        'Rejects an email with an invalid structure.'
        for address in INVALID_EXAMPLES:
            with self.assertRaises(
                    expected_exception=AddressFormatError,
                    msg=f'Test failed for {address}'):
                regex_check(EmailAddress(address))
