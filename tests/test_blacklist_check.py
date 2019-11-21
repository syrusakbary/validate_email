from os import makedirs
from os.path import dirname, join
from unittest.case import TestCase
from urllib.request import urlopen

from validate_email import validate_email
from validate_email.domainlist_check import domainlist_check

BLACKLIST_URL = (
    'https://raw.githubusercontent.com/martenson/disposable-email-domains/'
    'master/disposable_email_blocklist.conf')


class DlBlacklist(object):
    'Emulating downloading of blacklists on post-build command.'

    def __init__(self):
        from validate_email import domainlist_check
        self.build_lib = dirname(dirname(domainlist_check.__file__))

    def mkpath(self, name: str):
        'Emulate mkpath.'
        makedirs(name=name, exist_ok=True)

    def run(self):
        'Deploy function identical to the one in setup.py.'
        with urlopen(url=BLACKLIST_URL) as fd:
            content = fd.read().decode('utf-8')
        target_dir = join(self.build_lib, 'validate_email/lib')
        self.mkpath(name=target_dir)
        with open(join(target_dir, 'blacklist.txt'), 'w') as fd:
            fd.write(content)


class BlacklistCheckTestCase(TestCase):
    'Testing if the included blacklist filtering works.'

    def test_blacklist_positive(self):
        'Disallows blacklist item: mailinator.com.'
        dl = DlBlacklist()
        dl.run()
        domainlist_check._load_builtin_blacklist()
        self.assertFalse(expr=domainlist_check(
            email_address='pa2@mailinator.com'))
        self.assertFalse(expr=validate_email(
            email_address='pa2@mailinator.com', check_regex=False,
            use_blacklist=True))
        self.assertFalse(expr=validate_email(
            email_address='pa2@mailinator.com', check_regex=True,
            use_blacklist=True))

    def test_blacklist_negative(self):
        'Allows a domain not in the blacklist.'
        self.assertTrue(expr=domainlist_check(
            email_address='pa2@some-random-domain-thats-not-blacklisted.com'))

    def test_erroneous_email(self):
        'Will reject emails in erroneous format.'
        self.assertFalse(expr=domainlist_check(
            email_address='pa2-mailinator.com'))
