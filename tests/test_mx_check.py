from pyemailval.mx_check import _get_domain_from_email_address

DOMAINS = {
    'email@domain.com': 'domain.com',
    'email@subdomain.domain.com': 'subdomain.domain.com',
    'email@123.123.123.123': '123.123.123.123',
    'email@[123.123.123.123]': '123.123.123.123',
    'email@domain-one.com': 'domain-one.com',
    'email@domain.co.jp': 'domain.co.jp',
}


def test_domain_from_email_address():
    for email_address, domain in DOMAINS.items():
        try:
            domain_from_function = _get_domain_from_email_address(
                email_address)
            assert domain_from_function == domain
        except AssertionError:
            raise AssertionError(
                'Email address {} should result in domain {} but resulted in '
                'domain {}'.format(
                    email_address, domain, domain_from_function))
