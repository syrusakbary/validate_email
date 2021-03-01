# FAQ:

## The module provides false positives:

Some SMTP Servers (Yahoo's servers for example) are only rejecting
nonexistent emails after the end of `DATA` command has been provided in
the conversation with the server. This module only goes until the
`RCPT TO` and says it's valid if it doesn't get rejected there, since
the `DATA` part of the email is the email body itself. There's not much
one can do with it, you have to accept false positives in the case of
yahoo.com and some other providers. I'm not sure if rejecting emails
after the `DATA` command is a valid behavior based on the SMTP RFC, but
I wouldn't wonder if not.

## Everything gets rejected:

Check if you have port 25 access from your IP to the accepting server's
IP. Even if you do, the server might use RBL's (spamhaus.org lists, for
example), and your IP might get rejected because of being listed in one
of the used lists by the email server. Your best bet is to use this
module on another server that delivers emails, thus eliminating the
chance of being blacklisted.

## I can't check thousands of emails!

This module is a tool; every tool can become a weapon if not used
properly. In my case, I use this module to check email address validity
at registration time, so not thousands at once. Doing so might make you
(your IP) end up in one of the aforementioned blocklists, as providers
will detect you as a possible spammer. In short, I would advise against
your use case.

## My email doesn't check out!

Run this code with the module installed (use your parameters within),
and see the output:

```python
python -c 'import logging, sys; logging.basicConfig(stream=sys.stderr, level=logging.DEBUG); from validate_email import validate_email; print(validate_email(\'your.email@address.com\', check_mx=True, debug=True))'
```

If you still don't understand why your code doesn't work as expected by
looking at the the logs, then (and only then) add an issue explaining
your problem with a REPRODUCIBLE example, and the output of your test
run.

