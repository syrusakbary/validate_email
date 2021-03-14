from unittest.case import TestCase

from validate_email.domainlist_check import (
    domainlist_check, update_builtin_blacklist)
from validate_email.email_address import EmailAddress
from validate_email.exceptions import DomainBlacklistedError
from validate_email.validate_email import (
    validate_email, validate_email_or_fail)


class BlacklistCheckTestCase(TestCase):
    'Testing if the included blacklist filtering works.'

    def setUpClass():
        update_builtin_blacklist(force=False, background=False)

    def test_blacklist_positive(self):
        'Disallows blacklist item: mailinator.com.'
        with self.assertRaises(DomainBlacklistedError):
            domainlist_check(EmailAddress('pm2@mailinator.com'))
        with self.assertRaises(DomainBlacklistedError):
            validate_email_or_fail(
                email_address='pm2@mailinator.com', check_format=False,
                check_blacklist=True)
        with self.assertRaises(DomainBlacklistedError):
            validate_email_or_fail(
                email_address='pm2@mailinator.com', check_format=True,
                check_blacklist=True)
        with self.assertLogs():
            self.assertFalse(expr=validate_email(
                email_address='pm2@mailinator.com', check_format=False,
                check_blacklist=True))
        with self.assertLogs():
            self.assertFalse(expr=validate_email(
                email_address='pm2@mailinator.com', check_format=True,
                check_blacklist=True))

    def test_blacklist_negative(self):
        'Allows a domain not in the blacklist.'
        self.assertTrue(expr=domainlist_check(
            EmailAddress('pm2@some-random-domain-thats-not-blacklisted.com')))
