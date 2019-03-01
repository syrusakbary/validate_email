# All we are really doing is comparing the input string to one
# gigantic regular expression.  But building that regexp, and
# ensuring its correctness, is made much easier by assembling it
# from the "tokens" defined by the RFC.  Each of these tokens is
# tested in the accompanying unit test file.
#
# The section of RFC 2822 from which each pattern component is
# derived is given in an accompanying comment.
#
# https://tools.ietf.org/html/rfc2822
#
# (To make things simple, every string below is given as 'raw',
# even when it's not strictly necessary.  This way we don't forget
# when it is necessary.)
#


import re


WSP = r'\s'  # see 2.2.2. Structured Header Field Bodies
CRLF = r'(?:\r\n)'  # see 2.2.3. Long Header Fields
NO_WS_CTL = r'\x01-\x08\x0b\x0c\x0f-\x1f\x7f'  # see 3.2.1. Primitive Tokens
QUOTED_PAIR = r'(?:\\.)'  # see 3.2.2. Quoted characters
# see 3.2.3. Folding white space and comments
FWS = rf'(?:(?:{WSP}*{CRLF})?{WSP}+)'
CTEXT = rf'[{NO_WS_CTL}\x21-\x27\x2a-\x5b\x5d-\x7e]'  # see 3.2.3
# see 3.2.3 (NB: The RFC includes COMMENT here
CCONTENT = rf'(?:{CTEXT}|{QUOTED_PAIR})'
# as well, but that would be circular.)
COMMENT = rf'\((?:{FWS}?{CCONTENT})*{FWS}?\)'  # see 3.2.3
CFWS = rf'(?:{FWS}?{COMMENT})*(?:{FWS}?{COMMENT}|{FWS})'  # see 3.2.3
ATEXT = r'[\w!#$%&\'\*\+\-/=\?\^`\{\|\}~]'  # see 3.2.4. Atom
ATOM = rf'{CFWS}?{ATEXT}+{CFWS}?'  # see 3.2.4
DOT_ATOM_TEXT = rf'{ATEXT}+(?:\.{ATEXT}+)*'  # see 3.2.4
DOT_ATOM = rf'{CFWS}?{DOT_ATOM_TEXT}{CFWS}?'  # see 3.2.4
QTEXT = rf'[{NO_WS_CTL}\x21\x23-\x5b\x5d-\x7e]'  # see 3.2.5. Quoted strings
QCONTENT = rf'(?:{QTEXT}|{QUOTED_PAIR})'  # see 3.2.5
QUOTED_STRING = rf'{CFWS}?"(?:{FWS}?{QCONTENT})*{FWS}?"{CFWS}?'
# see 3.4.1. Addr-spec specification
LOCAL_PART = rf'(?:{DOT_ATOM}|{QUOTED_STRING})'
DTEXT = rf'[{NO_WS_CTL}\x21-\x5a\x5e-\x7e]'  # see 3.4.1
DCONTENT = rf'(?:{DTEXT}|{QUOTED_PAIR})'  # see 3.4.1
DOMAIN_LITERAL = rf'{CFWS}?\[(?:{FWS}?{DCONTENT})*{FWS}?\]{CFWS}?'  # see 3.4.1
DOMAIN = rf'(?:{DOT_ATOM}|{DOMAIN_LITERAL})'  # see 3.4.1
ADDR_SPEC = rf'{LOCAL_PART}@{DOMAIN}'  # see 3.4.1
VALID_ADDRESS_REGEXP = rf'^{ADDR_SPEC}$'

_matcher = re.compile(pattern=VALID_ADDRESS_REGEXP, flags=re.DOTALL)


def regex_check(email_address):
    if any(ord(char) > 127 for char in email_address):
        return False
    if _matcher.match(string=email_address):
        return True
    return False
