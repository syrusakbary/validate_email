import re
import socket
import smtplib
import dns.resolver as dns


def _get_domain_from_email_address(email_address):
    try:
        return re.search(r"(?<=@)\[?([^\[\]]+)", email_address)[1]
    except TypeError:
        raise ValueError("Invalid email address")
    except IndexError:
        raise ValueError("Invalid email address")


def _get_mx_records(domain):
    try:
        records = dns.query(domain, 'MX')
    except dns.NXDOMAIN:
        raise ValueError("Domain {} does not seem to exist")
    except:
        raise NotImplementedError("Feature not yet implemented")
    return [str(x.exchange) for x in records]


def mx_check(email_address, timeout=10):
    host = socket.gethostname()

    smtp = smtplib.SMTP(timeout=timeout)
    smtp.set_debuglevel(0)

    domain = _get_domain_from_email_address(email_address)
    mx_records = _get_mx_records(domain)

    for mx_record in mx_records:
        smtp.connect(mx_record)
        smtp.helo(host)
        smtp.mail(email_address)
        code, message = smtp.rcpt(email_address)
        smtp.quit()
        return True
        if code == 250:
            return True
    return False
