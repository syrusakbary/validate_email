==============
pyemailval
==============

pyemailval is a package for Python that check if an email is valid, properly formatted and really exists.



INSTALLATION
============

You can install the package with pip:

    pip install pyemailval


USAGE
=====

Basic usage::

    from pyemailval import validate_email
    is_valid = validate_email('example@example.com')


Checking domain has SMTP Server
-------------------------------

Check if the host has SMTP Server::

    from validate_email import validate_email
    is_valid = validate_email('example@example.com',check_mx=True)


Verify email exists
-------------------

Check if the host has SMTP Server and the email really exists::

    from validate_email import validate_email
    is_valid = validate_email('example@example.com',verify=True)


TODOs and BUGS
==============
See: http://github.com/Ben-Baert/pyemailval/issues