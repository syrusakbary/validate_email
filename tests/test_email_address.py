from unittest.case import TestCase

from validate_email import validate_email
from validate_email.email_address import EmailAddress
from validate_email.exceptions import AddressFormatError


class UserDomainTestCase(TestCase):
    'Test the split of an email address into user and domain.'

    valid_tests = {
        'email@domain.com': ('email', 'domain.com'),
        'email@subdomain.domain.com': ('email', 'subdomain.domain.com'),
        'email@123.123.123.123': ('email', '123.123.123.123'),
        'email@[123.123.123.123]': ('email', '[123.123.123.123]'),
        'email@domain-one.com': ('email', 'domain-one.com'),
        'email@domain.co.jp': ('email', 'domain.co.jp'),
    }

    invalid_tests = [
        'plainaddress',  # missing @ sign and domain
        'email.domain.com',  # missing @
    ]

    def test_user_domain_valid(self):
        'Splits email address into user and domain parts.'
        for address, (user, domain) in self.valid_tests.items():
            self.assertEqual(EmailAddress(address).user, user)
            self.assertEqual(EmailAddress(address).domain, domain)

    def test_user_domain_invalid(self):
        'Rejects unparseable email address.'
        for address in self.invalid_tests:
            # This must be rejected directly by the EmailAddress constructor...
            with self.assertRaises(AddressFormatError) as exc:
                EmailAddress(address)
            self.assertTupleEqual(exc.exception.args, ())
            # ...and indirectly by validate_email().
            self.assertFalse(validate_email(address))


class IdnaTestCase(TestCase):
    'Testing IDNA conversion.'

    valid_tests = {
        'email@address.com': 'email@address.com',
        'email@motörhéád.com': 'email@xn--motrhd-tta7d3f.com',
        'email@[123.123.123.123]': ('email@[123.123.123.123]'),
    }

    invalid_tests = [
        'test@♥web.de',
    ]

    def test_idna_conversion_valid(self):
        'Converts email address into ASCII-compatible encoding.'
        for address, ace in self.valid_tests.items():
            self.assertEqual(EmailAddress(address).ace, ace)

    def test_idna_conversion_invalid(self):
        'Rejects email address which is not IDNA-convertible.'
        for address in self.invalid_tests:
            # This must be rejected directly by the EmailAddress constructor...
            with self.assertRaises(AddressFormatError) as exc:
                EmailAddress(address)
            self.assertTupleEqual(exc.exception.args, ())
            # ...and indirectly by validate_email().
            self.assertFalse(validate_email(address))
