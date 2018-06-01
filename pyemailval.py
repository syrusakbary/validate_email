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


from email_regex import email_has_valid_structure
from mx_check import mx_check


def validate_email(
        email_address,
        check_structure=True,
        check_mx=True,
        smtp_timeout=10):

    if check_structure and not email_has_valid_structure(email_address):
        return False

    if not check_mx:
        return True

    return mx_check(email_address, timeout=smtp_timeout)
