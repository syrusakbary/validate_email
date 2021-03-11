from types import SimpleNamespace
from unittest.case import TestCase
from unittest.mock import Mock, patch

from dns.exception import Timeout

from validate_email import dns_check
from validate_email.dns_check import _get_cleaned_mx_records
from validate_email.exceptions import DNSTimeoutError, NoValidMXError


class DnsNameStub(object):
    'Stub for `dns.name.Name`.'

    def __init__(self, value: str):
        self.value = value

    def to_text(self) -> str:
        return self.value


class DnsRRsetStub(object):
    'Stub for `dns.rrset.RRset`.'

    def __init__(self, hostnames: list):
        self.names = [
            SimpleNamespace(exchange=DnsNameStub(value=x)) for x in hostnames]

    def processing_order(self):
        return self.names


def _answer(hostnames: list):
    return SimpleNamespace(rrset=DnsRRsetStub(hostnames=hostnames))


TEST_QUERY = Mock()


class GetMxRecordsTestCase(TestCase):
    'Testing `_get_mx_records`.'

    @patch.object(target=dns_check, attribute='resolve', new=TEST_QUERY)
    def test_fails_with_invalid_hostnames(self):
        'Fails when an MX hostname is "."'
        TEST_QUERY.return_value = _answer(hostnames=['.'])
        with self.assertRaises(NoValidMXError) as exc:
            _get_cleaned_mx_records(domain='testdomain1', timeout=10)
        self.assertTupleEqual(exc.exception.args, ())

    @patch.object(target=dns_check, attribute='resolve', new=TEST_QUERY)
    def test_fails_with_null_hostnames(self):
        'Fails when an MX hostname is invalid.'
        TEST_QUERY.return_value = _answer(hostnames=['asdqwe'])
        with self.assertRaises(NoValidMXError) as exc:
            _get_cleaned_mx_records(domain='testdomain2', timeout=10)
        self.assertTupleEqual(exc.exception.args, ())

    @patch.object(target=dns_check, attribute='resolve', new=TEST_QUERY)
    def test_filters_out_invalid_hostnames(self):
        'Returns only the valid hostnames.'
        TEST_QUERY.return_value = _answer(hostnames=[
            'asdqwe.',
            '.',
            'valid.host.',
            'valid.host.',  # This is an intentional duplicate.
            'valid2.host.',
        ])
        result = _get_cleaned_mx_records(domain='testdomain3', timeout=10)
        self.assertListEqual(result, ['valid.host', 'valid2.host'])

    @patch.object(target=dns_check, attribute='resolve', new=TEST_QUERY)
    def test_raises_exception_on_dns_timeout(self):
        'Raises exception on DNS timeout.'
        TEST_QUERY.side_effect = Timeout()
        with self.assertRaises(DNSTimeoutError) as exc:
            _get_cleaned_mx_records(domain='testdomain3', timeout=10)
        self.assertTupleEqual(exc.exception.args, ())
