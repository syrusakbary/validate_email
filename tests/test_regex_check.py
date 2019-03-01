from pyemailval.regex_check import regex_check
from unittest.case import TestCase

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
    'plainaddress',  # missing @ sign and domain
    '#@%^%#$@#$@#.com',  # garbage
    '@domain.com',  # missing username
    'Joe Smith <email@domain.com>',  # encoded html within email is invalid
    'email.domain.com',  # missing @
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


class RegexTest(TestCase):

    def test_valid_email_structure_regex(self):
        for address in VALID_EXAMPLES:
            self.assertTrue(
                expr=regex_check(address),
                msg=f'Check is not true with {address}')

    def test_invalid_email_structure_regex(self):
        for address in INVALID_EXAMPLES:
            self.assertFalse(
                expr=regex_check(address),
                msg=f'Check is true with {address}')
