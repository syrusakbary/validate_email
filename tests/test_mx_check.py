from unittest.case import TestCase
from pyemailval.mx_check import _get_domain_from_email_address

DOMAINS = {
    'email@domain.com': 'domain.com',
    'email@subdomain.domain.com': 'subdomain.domain.com',
    'email@123.123.123.123': '123.123.123.123',
    'email@[123.123.123.123]': '123.123.123.123',
    'email@domain-one.com': 'domain-one.com',
    'email@domain.co.jp': 'domain.co.jp',
}


class MxTestCase(TestCase):

    def test_domain_from_email_address(self):
        for address, domain in DOMAINS.items():
            domain_from_function = _get_domain_from_email_address(address)
            self.assertEqual(domain_from_function, domain)
