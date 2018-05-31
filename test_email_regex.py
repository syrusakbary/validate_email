from email_regex import get_domain_from_email_address
from email_regex import email_has_valid_structure

DOMAINS = {
    "email@domain.com": "domain.com",                 
    "email@subdomain.domain.com": "subdomain.domain.com",
    "email@123.123.123.123": "123.123.123.123",
    "email@[123.123.123.123]": "123.123.123.123",
    "email@domain-one.com": "domain-one.com",
    "email@domain.co.jp": "domain.co.jp",
}

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


def test_domain_from_email_address():
    for email_address, domain in DOMAINS.items():
        try:
            domain_from_function = get_domain_from_email_address(email_address)
            assert domain_from_function == domain
        except AssertionError:
            raise AssertionError(
                "Email address {} should result in domain {} but resulted in domain {}"
                    .format(email_address, domain, domain_from_function))


def test_valid_email_structure_regex():
    for index, valid_email_address in enumerate(VALID_EMAIL_ADDRESS_EXAMPLES):
        try:
            assert email_has_valid_structure(valid_email_address) is True
        except AssertionError:
            raise AssertionError(
                "{} should be valid ({}th email address in the list)"
                    .format(valid_email_address, index))

def test_invalid_email_structure_regex():
    for index, invalid_email_address in enumerate(INVALID_EMAIL_ADDRESS_EXAMPLES):
        try:
            assert email_has_valid_structure(invalid_email_address) is False
        except AssertionError:
            raise AssertionError(
                "{} should be invalid ({}th email address in the list)"
                    .format(invalid_email_address, index))
