from email_regex import email_has_valid_structure

VALID_EMAIL_ADDRESS_EXAMPLES = [
    "email@domain.com",                 # basic valid email
    "firstname.lastname@domain.com",    # dot in address field
    "email@subdomain.domain.com",       # dot in subdomain
    "firstname+lastname@domain.com",    # + in address field
    "email@123.123.123.123",            # domain address is IP address
    "email@[123.123.123.123]",          # square brackets around IP address
    "\"email\"@domain.com",             # quote marks in address fields
    "1234567890@domain.com",            # numbers in address field
    "email@domain-one.com",             # dash in subdomain
    "_______@domain.com",               # underscore in address field
    "email@domain.name",                # .name top level domain name
    "email@domain.co.jp",               # dot in top level domain
    "firstname-lastname@domain.com"     # dash in address field
]

INVALID_EMAIL_ADDRESS_EXAMPLES = [
    "plainaddress",                     # missing @ sign and domain
    "#@%^%#$@#$@#.com",                 # garbage
    "@domain.com",                      # missing username
    "Joe Smith <email@domain.com>",     # encoded html within email is invalid
    "email.domain.com",                 # missing @
    "email@domain@domain.com",          # two @ sign
    ".email@domain.com",                # leading dot in address is not allowed
    "email.@domain.com",                # trailing dot in address is not allowed
    "email..email@domain.com",          # multiple dots
    "あいうえお@domain.com",              # unicode char as address
    "email@domain.com (Joe Smith)",     # text followed email is not allowed
    "email@domain",                     # missing top level domain (.com/.net/.org/etc)
    "email@-domain.com",                # leading dash in front of domain is invalid
    "email@domain.web",                 # .web is not a valid top level domain
    "email@111.222.333.44444",          # invalid IP format
    "email@domain..com",                # multiple dot in the domain portion is invalid
]


def test_valid_email_structure_regex():
    for index, valid_email_address in enumerate(VALID_EMAIL_ADDRESS_EXAMPLES):
        try:
            assert email_has_valid_structure(valid_email_address) is True
        except AssertionError:
            raise AssertionError(
                ("{} should be valid ({}th email address in the list)"
                    .format(valid_email_address, index)))

def test_invalid_email_structure_regex():
    for index, invalid_email_address in enumerate(INVALID_EMAIL_ADDRESS_EXAMPLES):
        try:
            assert email_has_valid_structure(invalid_email_address) is False
        except AssertionError:
            raise AssertionError(
                ("{} should be invalid ({}th email address in the list)"
                    .format(invalid_email_address, index)))
