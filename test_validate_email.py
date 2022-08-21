import validate_email


def test_validate_email():
    assert validate_email.validate_email("me@syrusakbary.com")


def test_validate_email_with_check_mx():
    assert validate_email.validate_email("me@syrusakbary.com", check_mx=True)
