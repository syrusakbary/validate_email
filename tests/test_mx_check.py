from smtplib import SMTP, SMTPResponseException
from types import SimpleNamespace
from unittest.case import TestCase
from unittest.mock import Mock, patch

from dns.exception import Timeout

from validate_email import mx_check as mx_module
from validate_email.email_address import EmailAddress
from validate_email.exceptions import (
    DNSTimeoutError, NoValidMXError, SMTPCommunicationError, SMTPMessage,
    SMTPTemporaryError)
from validate_email.mx_check import (
    _get_cleaned_mx_records, _SMTPChecker, mx_check)


class DnsNameStub(object):
    'Stub for `dns.name.Name`.'

    def __init__(self, value: str):
        self.value = value

    def to_text(self) -> str:
        return self.value


TEST_QUERY = Mock()


class GetMxRecordsTestCase(TestCase):
    'Testing `_get_mx_records`.'

    @patch.object(target=mx_module, attribute='resolve', new=TEST_QUERY)
    def test_fails_with_invalid_hostnames(self):
        'Fails when an MX hostname is "."'
        TEST_QUERY.return_value = [
            SimpleNamespace(exchange=DnsNameStub(value='.'))]
        with self.assertRaises(NoValidMXError) as exc:
            _get_cleaned_mx_records(domain='testdomain1', timeout=10)
        self.assertTupleEqual(exc.exception.args, ())

    @patch.object(target=mx_module, attribute='resolve', new=TEST_QUERY)
    def test_fails_with_null_hostnames(self):
        'Fails when an MX hostname is invalid.'
        TEST_QUERY.return_value = [
            SimpleNamespace(exchange=DnsNameStub(value='asdqwe'))]
        with self.assertRaises(NoValidMXError) as exc:
            _get_cleaned_mx_records(domain='testdomain2', timeout=10)
        self.assertTupleEqual(exc.exception.args, ())

    @patch.object(target=mx_module, attribute='resolve', new=TEST_QUERY)
    def test_filters_out_invalid_hostnames(self):
        'Returns only the valid hostnames.'
        TEST_QUERY.return_value = [
            SimpleNamespace(exchange=DnsNameStub(value='asdqwe.')),
            SimpleNamespace(exchange=DnsNameStub(value='.')),
            SimpleNamespace(exchange=DnsNameStub(value='valid.host.')),
            # This is an intentional duplicate.
            SimpleNamespace(exchange=DnsNameStub(value='valid.host.')),
            SimpleNamespace(exchange=DnsNameStub(value='valid2.host.')),
        ]
        result = _get_cleaned_mx_records(domain='testdomain3', timeout=10)
        self.assertListEqual(result, ['valid.host', 'valid2.host'])

    @patch.object(target=mx_module, attribute='resolve', new=TEST_QUERY)
    def test_raises_exception_on_dns_timeout(self):
        'Raises exception on DNS timeout.'
        TEST_QUERY.side_effect = Timeout()
        with self.assertRaises(DNSTimeoutError) as exc:
            _get_cleaned_mx_records(domain='testdomain3', timeout=10)
        self.assertTupleEqual(exc.exception.args, ())

    @patch.object(target=_SMTPChecker, attribute='check')
    def test_skip_smtp_argument(self, check_mx_records_mock):
        'Check correct work of `skip_smtp` argument.'
        self.assertTrue(mx_check(
            EmailAddress('test@mail.ru'), debug=False, skip_smtp=True))
        self.assertEqual(check_mx_records_mock.call_count, 0)
        check_mx_records_mock.call_count


class SMTPCheckerTest(TestCase):
    'Checking the `_SMTPChecker` class functions.'

    @patch.object(target=SMTP, attribute='connect')
    def test_connect_raises_serverdisconnected(self, mock_connect):
        'Connect raises `SMTPServerDisconnected`.'
        mock_connect.side_effect = OSError('test message')
        checker = _SMTPChecker(
            local_hostname='localhost', timeout=5, debug=False,
            sender='test@example.com', recip='test@example.com')
        with self.assertRaises(SMTPCommunicationError) as exc:
            checker.check(hosts=['testhost'])
        self.assertDictEqual(exc.exception.error_messages, {
            'testhost': SMTPMessage(
                command='connect', code=0, text='test message')
        })

    @patch.object(target=SMTP, attribute='connect')
    def test_connect_with_error(self, mock_connect):
        'Connect raises `SMTPServerDisconnected`.'
        checker = _SMTPChecker(
            local_hostname='localhost', timeout=5, debug=False,
            sender='test@example.com', recip='test@example.com')
        mock_connect.return_value = (400, b'test delay message')
        with self.assertRaises(SMTPTemporaryError) as exc:
            checker.check(hosts=['testhost'])
        self.assertDictEqual(exc.exception.error_messages, {
            'testhost': SMTPMessage(
                command='connect', code=400, text='test delay message')
        })
