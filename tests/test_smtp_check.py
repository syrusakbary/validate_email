from smtplib import SMTP
from unittest.case import TestCase
from unittest.mock import patch

from validate_email.exceptions import SMTPMessage, SMTPTemporaryError
from validate_email.smtp_check import _SMTPChecker


class SMTPCheckerTest(TestCase):
    'Checking the `_SMTPChecker` class methods.'

    @patch.object(target=SMTP, attribute='connect')
    def test_connect_raises_serverdisconnected(self, mock_connect):
        'Connect raises `SMTPTemporaryError`.'
        mock_connect.side_effect = OSError('test message')
        checker = _SMTPChecker(
            local_hostname='localhost', timeout=5, debug=False,
            sender='test@example.com', recip='test@example.com')
        with self.assertRaises(SMTPTemporaryError) as exc:
            checker.check(hosts=['testhost'])
        self.assertDictEqual(exc.exception.error_messages, {
            'testhost': SMTPMessage(
                command='connect', code=451, text='test message')
        })

    @patch.object(target=SMTP, attribute='connect')
    def test_connect_with_error(self, mock_connect):
        'Connect raises `SMTPTemporaryError`.'
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
