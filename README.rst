.. image:: https://travis-ci.org/karolyi/py3-validate-email.svg?branch=master
    :target: https://travis-ci.org/karolyi/py3-validate-email

==============
py3-validate-email
==============

py3-validate-email is a package for Python that check if an email is valid, properly formatted and really exists.



INSTALLATION
============

You can install the package with pip:

    pip install py3-validate-email


USAGE
=====

Basic usage::

    from validate_email import validate_email
    is_valid = validate_email('example@example.com', check_regex=True, check_mx=True)

check_regex will check will the email address has a valid structure and defaults to True
check_mx will check the mx-records and check whether the email actually exists


TODOs and BUGS
==============
See: https://github.com/karolyi/py3-validate-email/issues
