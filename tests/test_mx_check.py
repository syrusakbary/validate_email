from types import SimpleNamespace
from unittest.case import TestCase
from unittest.mock import Mock, patch

from dns.exception import Timeout

from validate_email import mx_check as mx_module
from validate_email.email_address import EmailAddress
from validate_email.exceptions import DNSTimeoutError, NoValidMXError
from validate_email.mx_check import _get_mx_records, mx_check


class DnsNameStub(object):
    'Stub for `dns.name.Name`.'

    def __init__(self, value: str):
        self.value = value

    def to_text(self) -> str:
        return self.value


TEST_QUERY = Mock()


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

    @patch.object(target=mx_module, attribute='_check_mx_records')
    def test_no_smtp_argument(self, check_mx_records_mock):
        'Check correct work of no_smtp argument.'

        self.assertTrue(
            mx_check(EmailAddress('test@mail.ru'), debug=False, no_smtp=True)
        )
        self.assertEqual(check_mx_records_mock.call_count, 0)
