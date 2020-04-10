from types import SimpleNamespace
from unittest.case import TestCase
from unittest.mock import Mock, patch

from dns.exception import Timeout

from validate_email import mx_check as mx_module
from validate_email.exceptions import (
    AddressFormatError, DNSTimeoutError, NoValidMXError)
from validate_email.mx_check import (
    _dissect_email, _get_idna_address, _get_mx_records)

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
            _user, domain_from_function = _dissect_email(email_address=address)
            self.assertEqual(domain_from_function, domain)


class IdnaTestCase(TestCase):
    'Testing IDNA converting.'

    def test_resolves_idna_domains(self):
        'Resolves email@motörhéád.com.'
        self.assertEqual(
            first=_get_idna_address(email_address='email@motörhéád.com'),
            second='email@xn--motrhd-tta7d3f.com')

    def test_resolves_conventional_domains(self):
        'Resolves email@address.com.'
        self.assertEqual(
            first=_get_idna_address(email_address='email@address.com'),
            second='email@address.com')


class GetMxRecordsTestCase(TestCase):
    'Testing `_get_mx_records`.'

    @patch.object(target=mx_module, attribute='query', new=TEST_QUERY)
    def test_fails_with_invalid_hostnames(self):
        'Fails when an MX hostname is "."'
        TEST_QUERY.return_value = [
            SimpleNamespace(exchange=DnsNameStub(value='.'))]
        with self.assertRaises(NoValidMXError) as exc:
            _get_mx_records(domain='testdomain1', timeout=10)
        self.assertTupleEqual(exc.exception.args, ())

    @patch.object(target=mx_module, attribute='query', new=TEST_QUERY)
    def test_fails_with_null_hostnames(self):
        'Fails when an MX hostname is invalid.'
        TEST_QUERY.return_value = [
            SimpleNamespace(exchange=DnsNameStub(value='asdqwe'))]
        with self.assertRaises(NoValidMXError) as exc:
            _get_mx_records(domain='testdomain2', timeout=10)
        self.assertTupleEqual(exc.exception.args, ())

    @patch.object(target=mx_module, attribute='query', new=TEST_QUERY)
    def test_filters_out_invalid_hostnames(self):
        'Returns only the valid hostnames.'
        TEST_QUERY.return_value = [
            SimpleNamespace(exchange=DnsNameStub(value='asdqwe.')),
            SimpleNamespace(exchange=DnsNameStub(value='.')),
            SimpleNamespace(exchange=DnsNameStub(value='valid.host.')),
            SimpleNamespace(exchange=DnsNameStub(value='valid2.host.')),
        ]
        result = _get_mx_records(domain='testdomain3', timeout=10)
        self.assertListEqual(result, ['valid.host.', 'valid2.host.'])

    @patch.object(target=mx_module, attribute='query', new=TEST_QUERY)
    def test_raises_exception_on_dns_timeout(self):
        'Raises exception on DNS timeout.'
        TEST_QUERY.side_effect = Timeout()
        with self.assertRaises(DNSTimeoutError) as exc:
            _get_mx_records(domain='testdomain3', timeout=10)
        self.assertTupleEqual(exc.exception.args, ())

    def test_returns_false_on_idna_failure(self):
        'Returns `False` on IDNA failure.'
        with self.assertRaises(AddressFormatError) as exc:
            mx_module.mx_check(
                email_address='test@♥web.de', from_address='mail@example.com')
        self.assertTupleEqual(exc.exception.args, ())
