from smtplib import SMTPServerDisconnected
from socket import timeout
from unittest.case import TestCase
from unittest.mock import patch

from validate_email.email_address import EmailAddress
from validate_email.exceptions import (
    AddressNotDeliverableError, SMTPCommunicationError, SMTPTemporaryError)
from validate_email.smtp_check import _SMTPChecker, smtp_check


class SMTPMock(_SMTPChecker):
    """
    Mock replacement for the SMTP connection.

    Instead of really communicating with an SMTP server, this class
    works with predefined fake responses. By default, the responses
    emulate a successful SMTP conversation, but it can be turned into an
    unsuccessful one by patching the `reply` dictionary.
    """
    reply = {
        None: (220, b'Welcome'),
        "EHLO": (502, b'Please use HELO'),
        'HELO': (220, b'HELO successful'),
        'MAIL': (250, b'MAIL FROM successful'),
        'RCPT': (250, b'RCPT TO successful'),
        'QUIT': (221, b'QUIT successful'),
    }

    last_command = None

    def _get_socket(self, host, port, timeout):
        return None

    def send(self, s):
        self.last_command = s[:4].upper()

    def getreply(self):
        if isinstance(self.reply[self.last_command], Exception):
            self.close()
            raise self.reply[self.last_command]
        return self.reply[self.last_command]


class SMTPCheckTest(TestCase):
    'Collection of tests the `smtp_check` method.'

    # All the possible ways to fail we want to test, listed as tuples
    # containing (command, reply, expected exception).
    failures = [
        # Timeout on connection
        (None, timeout(), SMTPTemporaryError),
        # Connection unexpectedly closed during any stage
        (None, SMTPServerDisconnected('Test'), SMTPTemporaryError),
        ('EHLO', SMTPServerDisconnected('Test'), SMTPTemporaryError),
        ('HELO', SMTPServerDisconnected('Test'), SMTPTemporaryError),
        ('MAIL', SMTPServerDisconnected('Test'), SMTPTemporaryError),
        ('RCPT', SMTPServerDisconnected('Test'), SMTPTemporaryError),
        # Temporary error codes
        (None, (421, b'Connect failed'), SMTPTemporaryError),
        ('HELO', (421, b'HELO failed'), SMTPTemporaryError),
        ('MAIL', (451, b'MAIL FROM failed'), SMTPTemporaryError),
        ('RCPT', (451, b'RCPT TO failed'), SMTPTemporaryError),
        # Permanent error codes
        (None, (554, b'Connect failed'), SMTPCommunicationError),
        ('HELO', (504, b'HELO failed'), SMTPCommunicationError),
        ('MAIL', (550, b'MAIL FROM failed'), SMTPCommunicationError),
        ('RCPT', (550, b'RCPT TO failed'), AddressNotDeliverableError),
    ]

    @patch(target='validate_email.smtp_check._SMTPChecker', new=SMTPMock)
    def test_smtp_success(self):
        'Succeeds on successful SMTP conversation'
        self.assertTrue(
            smtp_check(
                email_address=EmailAddress('alice@example.com'),
                mx_records=['smtp.example.com'],
            )
        )

    def _test_one_smtp_failure(self, cmd, reply, exception):
        with patch.dict(in_dict=SMTPMock.reply, values={cmd: reply}):
            with self.assertRaises(exception) as context:
                smtp_check(
                    email_address=EmailAddress('alice@example.com'),
                    mx_records=['smtp.example.com'],
                )
            if isinstance(reply, tuple):
                error_messages = context.exception.error_messages
                error_info = error_messages['smtp.example.com']
                self.assertEqual(error_info.command[:4].upper(), cmd or 'CONN')
                self.assertEqual(error_info.code, reply[0])
                self.assertEqual(error_info.text, reply[1].decode())

    @patch(target='validate_email.smtp_check._SMTPChecker', new=SMTPMock)
    def test_smtp_failure(self):
        'Fails on unsuccessful SMTP conversation.'
        for cmd, reply, exception in self.failures:
            with self.subTest(cmd=cmd, reply=reply):
                self._test_one_smtp_failure(cmd, reply, exception)
