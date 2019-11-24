from unittest.case import TestCase

from validate_email import validate_email
from validate_email.domainlist_check import BlacklistUpdater, domainlist_check


class BlacklistCheckTestCase(TestCase):
    'Testing if the included blacklist filtering works.'

    def setUpClass():
        blacklist_updater = BlacklistUpdater()
        blacklist_updater.process()

    def test_blacklist_positive(self):
        'Disallows blacklist item: mailinator.com.'
        domainlist_check._load_builtin_blacklist()
        self.assertFalse(expr=domainlist_check(
            user_part='pa2', domain_part='mailinator.com'))
        self.assertFalse(expr=validate_email(
            email_address='pa2@mailinator.com', check_regex=False,
            use_blacklist=True))
        self.assertFalse(expr=validate_email(
            email_address='pa2@mailinator.com', check_regex=True,
            use_blacklist=True))

    def test_blacklist_negative(self):
        'Allows a domain not in the blacklist.'
        self.assertTrue(expr=domainlist_check(
            user_part='pa2',
            domain_part='some-random-domain-thats-not-blacklisted.com'))
