# FAQ:

## The module provides false positives:

The function of this module, and specifically of the SMTP check, relies
on the assumption that the mail server declared responsible for an email
domain will immediately reject any nonexistent address.

Some SMTP servers (Yahoo's servers for example) are only rejecting
nonexistent emails after the end of `DATA` command has been provided in
the conversation with the server. This module only goes until the
`RCPT TO` and says it's valid if it doesn't get rejected there, since
the `DATA` part of the email is the email body itself.

Other SMTP servers accept emails even for nonexistent recipient
addresses and forward them to a different server which will create a
bounce message in a second step. This is the case for many email domains
hosted at Microsoft.

In both cases, there's nothing we can do about it, as the mail server
we talk to seemingly accepts the email address.

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
python -c 'import logging, sys; logging.basicConfig(stream=sys.stderr, level=logging.DEBUG); from validate_email import validate_email; print(validate_email(\'your.email@address.com\', smtp_debug=True))'
```

If you still don't understand why your code doesn't work as expected by
looking at the the logs, then (and only then) add an issue explaining
your problem with a REPRODUCIBLE example, and the output of your test
run.

## How can I pass my email account's credentials? How can I use port 465 or 587 when my provider blocks port 25?

The credentials you got from your email provider, as well as the
instruction to use port 465 or 587, refer to *your provider's* server
for *outgoing* emails.

This module, however, directly talks to the *recipient's* server for
*incoming* emails, so neither your credentials nor the switch to port
465 or 587 is of any use here.

If your internet connection is within an IP pool (often the case for
private use) or it doesn't have a proper reverse DNS entry, the servers
for many email domains (depending on their configuration) will reject
connections from you. This can *not* be solved by using your provider's
mail server. Instead, you have to use the library on a machine with an
internet connection with static IP address and a proper reverse DNS
entry.
