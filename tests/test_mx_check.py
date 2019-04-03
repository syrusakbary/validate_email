from types import SimpleNamespace
from unittest.case import TestCase
from unittest.mock import Mock, patch

from validate_email import mx_check as mx_module
from validate_email.mx_check import (
    _get_domain_from_email_address, _get_mx_records)

DOMAINS = {
    'email@domain.com': 'domain.com',
    'email@subdomain.domain.com': 'subdomain.domain.com',
    'email@123.123.123.123': '123.123.123.123',
    'email@[123.123.123.123]': '123.123.123.123',
    'email@domain-one.com': 'domain-one.com',
    'email@domain.co.jp': 'domain.co.jp',
}


class DnsNameStub(object):
    'Stub for `dns.name.Name`.'

    def __init__(self, value: str):
        self.value = value

    def to_text(self) -> str:
        return self.value


TEST_QUERY = Mock()


class DomainTestCase(TestCase):

    def test_domain_from_email_address(self):
        for address, domain in DOMAINS.items():
            domain_from_function = _get_domain_from_email_address(address)
            self.assertEqual(domain_from_function, domain)


class GetMxRecordsTestCase(TestCase):
    'Testing `_get_mx_records`.'

    @patch.object(target=mx_module, attribute='query', new=TEST_QUERY)
    def test_fails_with_invalid_hostnames(self):
        'Fails when an MX hostname is "."'
        TEST_QUERY.return_value = [
            SimpleNamespace(exchange=DnsNameStub(value='.'))]
        with self.assertRaises(ValueError) as exc:
            _get_mx_records(domain='testdomain1')
        self.assertEqual(
            exc.exception.args[0],
            'Domain testdomain1 does not have a valid MX record')

    @patch.object(target=mx_module, attribute='query', new=TEST_QUERY)
    def test_fails_with_null_hostnames(self):
        'Fails when an MX hostname is invalid.'
        TEST_QUERY.return_value = [
            SimpleNamespace(exchange=DnsNameStub(value='asdqwe'))]
        with self.assertRaises(ValueError) as exc:
            _get_mx_records(domain='testdomain2')
        self.assertEqual(
            exc.exception.args[0],
            'Domain testdomain2 does not have a valid MX record')

    @patch.object(target=mx_module, attribute='query', new=TEST_QUERY)
    def test_filters_out_invalid_hostnames(self):
        'Returns only the valid hostnames.'
        TEST_QUERY.return_value = [
            SimpleNamespace(exchange=DnsNameStub(value='asdqwe.')),
            SimpleNamespace(exchange=DnsNameStub(value='.')),
            SimpleNamespace(exchange=DnsNameStub(value='valid.host.')),
            SimpleNamespace(exchange=DnsNameStub(value='valid2.host.')),
        ]
        result = _get_mx_records(domain='testdomain3')
        self.assertListEqual(result, ['valid.host.', 'valid2.host.'])
