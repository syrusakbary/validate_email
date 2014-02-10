# RFC 2822 - style email validation for Python
# (c) 2012 Syrus Akbary <me@syrusakbary.com>
# Extended from (c) 2011 Noel Bush <noel@aitools.org>
# for support of mx and user check
# This code is made available to you under the GNU LGPL v3.
#
# This module provides a single method, valid_email_address(),
# which returns True or False to indicate whether a given address
# is valid according to the 'addr-spec' part of the specification
# given in RFC 2822.  Ideally, we would like to find this
# in some other library, already thoroughly tested and well-
# maintained.  The standard Python library email.utils
# contains a parse_addr() function, but it is not sufficient
# to detect many malformed addresses.
#
# This implementation aims to be faithful to the RFC, with the
# exception of a circular definition (see comments below), and
# with the omission of the pattern components marked as "obsolete".

import functools
import itertools
import logging
import optparse
import re
import smtplib
import socket
import sys
import time
from multiprocessing import Pool

try:
    import DNS
    DNS.DiscoverNameServers()
except ImportError:
    DNS = None

# All we are really doing is comparing the input string to one
# gigantic regular expression.  But building that regexp, and
# ensuring its correctness, is made much easier by assembling it
# from the "tokens" defined by the RFC.  Each of these tokens is
# tested in the accompanying unit test file.
#
# The section of RFC 2822 from which each pattern component is
# derived is given in an accompanying comment.
#
# (To make things simple, every string below is given as 'raw',
# even when it's not strictly necessary.  This way we don't forget
# when it is necessary.)

WSP = r'[ \t]'                                       # see 2.2.2. Structured Header Field Bodies
CRLF = r'(?:\r\n)'                                   # see 2.2.3. Long Header Fields
NO_WS_CTL = r'\x01-\x08\x0b\x0c\x0f-\x1f\x7f'        # see 3.2.1. Primitive Tokens
QUOTED_PAIR = r'(?:\\.)'                             # see 3.2.2. Quoted characters
FWS = r'(?:(?:' + WSP + r'*' + CRLF + r')?' + \
      WSP + r'+)'                                    # see 3.2.3. Folding white space and comments
CTEXT = r'[' + NO_WS_CTL + \
        r'\x21-\x27\x2a-\x5b\x5d-\x7e]'              # see 3.2.3
CCONTENT = r'(?:' + CTEXT + r'|' + \
           QUOTED_PAIR + r')'                        # see 3.2.3 (NB: The RFC includes COMMENT here
# as well, but that would be circular.)
COMMENT = r'\((?:' + FWS + r'?' + CCONTENT + \
          r')*' + FWS + r'?\)'                       # see 3.2.3
CFWS = r'(?:' + FWS + r'?' + COMMENT + ')*(?:' + \
       FWS + '?' + COMMENT + '|' + FWS + ')'         # see 3.2.3
ATEXT = r'[\w!#$%&\'\*\+\-/=\?\^`\{\|\}~]'           # see 3.2.4. Atom
ATOM = CFWS + r'?' + ATEXT + r'+' + CFWS + r'?'      # see 3.2.4
DOT_ATOM_TEXT = ATEXT + r'+(?:\.' + ATEXT + r'+)*'   # see 3.2.4
DOT_ATOM = CFWS + r'?' + DOT_ATOM_TEXT + CFWS + r'?' # see 3.2.4
QTEXT = r'[' + NO_WS_CTL + \
        r'\x21\x23-\x5b\x5d-\x7e]'                   # see 3.2.5. Quoted strings
QCONTENT = r'(?:' + QTEXT + r'|' + \
           QUOTED_PAIR + r')'                        # see 3.2.5
QUOTED_STRING = CFWS + r'?' + r'"(?:' + FWS + \
                r'?' + QCONTENT + r')*' + FWS + \
                r'?' + r'"' + CFWS + r'?'
LOCAL_PART = r'(?:' + DOT_ATOM + r'|' + \
             QUOTED_STRING + r')'                    # see 3.4.1. Addr-spec specification
DTEXT = r'[' + NO_WS_CTL + r'\x21-\x5a\x5e-\x7e]'    # see 3.4.1
DCONTENT = r'(?:' + DTEXT + r'|' + \
           QUOTED_PAIR + r')'                        # see 3.4.1
DOMAIN_LITERAL = CFWS + r'?' + r'\[' + \
                 r'(?:' + FWS + r'?' + DCONTENT + \
                 r')*' + FWS + r'?\]' + CFWS + r'?'  # see 3.4.1
DOMAIN = r'(?:' + DOT_ATOM + r'|' + \
         DOMAIN_LITERAL + r')'                       # see 3.4.1
ADDR_SPEC = LOCAL_PART + r'@' + DOMAIN               # see 3.4.1

# A valid address will match exactly the 3.4.1 addr-spec.
VALID_ADDRESS_REGEXP = '^' + ADDR_SPEC + '$'

MX_DNS_CACHE = {}
SMTP_CACHE = {}


def iter_rate_limit(rate, iterable):
    iterator = iter(iterable)
    if not callable(rate):
        # constant rate
        rate_0 = rate
        rate = lambda t: rate_0

    t = t0 = time.time()
    yield next(iterator)

    for x in iterator:
        dt = (1. / rate(t - t0)) - (time.time() - t)
        if dt > 0:
            time.sleep(dt)

        t = time.time()
        yield x


def pmap(iterable, func, workers, rate=0):
    if rate:
        iterable = iter_rate_limit(rate, iterable)
    if workers == 1:
        for r in itertools.imap(func, iterable):
            yield r
    else:
        pool = Pool(processes=workers)
        for r in pool.imap_unordered(func, iterable):
            yield r


def get_mx_ip(hostname):
    try:
        return MX_DNS_CACHE[hostname]
    except KeyError:
        mx_hosts = DNS.mxlookup(hostname)
        MX_DNS_CACHE[hostname] = mx_hosts
        return mx_hosts


def connect_smtp(email, mx, check_mx, verify, timeout):
    mx_server = mx[1] if isinstance(mx, tuple) else mx
    try:
        smtp = SMTP_CACHE[mx_server]
        # smtp.connect()
    except KeyError:
        try:
            smtp = smtplib.SMTP(mx_server, 25, timeout=timeout)
        except socket.timeout:
            smtp = smtplib.SMTP(mx_server, 587, timeout=timeout)

        SMTP_CACHE[mx] = smtp

    if not verify:
        return True  # Valid

    status, _ = smtp.helo()
    if status != 250:
        return False  # Continue

    smtp.mail('')
    status, _ = smtp.rcpt(email)
    if status == 250:
        return True  # Valid



def validate_email(email, check_mx=False, verify=False,
                   timeout=10, debug=False):
    """Indicate whether the given string is a valid email address
    according to the 'addr-spec' portion of RFC 2822 (see section
    3.4.1).  Parts of the spec that are marked obsolete are *not*
    included in this test, and certain arcane constructions that
    depend on circular definitions in the spec may not pass, but in
    general this should correctly identify any email address likely
    to be in use as of 2011."""
    if debug:
        logger = logging.getLogger('validate_email')
        logger.setLevel(logging.DEBUG)
    else:
        logger = None

    email = email.strip()

    try:
        assert re.match(VALID_ADDRESS_REGEXP, email) is not None
    except AssertionError:
        return email, False  # Invalid

    check_mx |= verify

    if check_mx:
        return email, True

    if not DNS:
        raise Exception('For check the mx records or check if '
                        'the email exists you must have '
                        'installed pyDNS python package')

    hostname = email[email.find('@') + 1:]

    try:
        mx_hosts = get_mx_ip(hostname)

    except DNS.Base.TimeoutError:
        return email, None  # Not sure

    except DNS.ServerError:
        return email, False  # Invalid

    for mx in mx_hosts:
        try:
            if connect_smtp(email, mx, check_mx, verify, timeout):
                return email, True  # Verified

        except smtplib.SMTPServerDisconnected:
            break  # Server not permits verify user

        except smtplib.SMTPConnectError:
            continue

        except socket.timeout:
            continue

        except socket.error:
            continue

    return email, None  # Not sure


def run(email=None, input_file=None, check_mx=False, verify=False,
        workers=10, rate=10, timeout=10, debug=False):
    if email:
        print validate_email(email, verify=True)
        return 0

    func = functools.partial(validate_email,
                             check_mx=check_mx, verify=verify, timeout=timeout)
    with open(input_file) as f:
        with open('valid-%s' % input_file, 'w', 0) as f_valid:
            with open('invalid-%s' % input_file, 'w', 0) as f_invalid:
                for email, result in pmap(f, func, workers, rate):
                    if result:
                        f_valid.write(email)
                        f_valid.write('\n')
                    else:
                        f_invalid.write(email)
                        f_invalid.write('\n')

                # for smtp in SMTP_CACHE.itervalues():
                #     if smtp:
                #         smtp.quit()

    return 0


def parse_args(args):
    parser = optparse.OptionParser(
        usage="email_verification [options]",
        description="Description: Basic email verification",
        epilog="**Example: email_verification --email=test@example.com")
    parser.add_option(
        '--email', dest='email',
        help='Email address we want to verify',
        default=None)
    parser.add_option(
        '--input-file', dest='input_file',
        help='Filename with the list of email addresses we want to verify',
        default=None)
    parser.add_option("-r", type="int", dest="rate", default=10)
    parser.add_option("-t", type="int", dest="timeout", default=10)
    parser.add_option("-w", type="int", dest="workers", default=10)
    parser.add_option(
        '--check-mx', dest='check_mx', action='store_true',
        help='Check if the host has SMTP Server', default=False)
    parser.add_option(
        '--verify', dest='verify', action='store_true',
        help='Check if the host has SMTP Server and the email really exists',
        default=False)
    parser.add_option(
        '--debug', dest='debug', action='store_true',
        help='show debugging messages', default=False)

    params, args = parser.parse_args(list(args))
    return params.__dict__


def main(*args):
    params = parse_args(args)
    return run(**params)


if __name__ == '__main__':
    main(*sys.argv[1:])
