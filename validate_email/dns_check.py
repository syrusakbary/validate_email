from dns.exception import Timeout
from dns.rdatatype import MX as rdtype_mx
from dns.rdtypes.ANY.MX import MX
from dns.resolver import (
    NXDOMAIN, YXDOMAIN, Answer, NoAnswer, NoNameservers, resolve)

from .constants import HOST_REGEX
from .email_address import EmailAddress
from .exceptions import (
    DNSConfigurationError, DNSTimeoutError, DomainNotFoundError, NoMXError,
    NoNameserverError, NoValidMXError)


def _get_mx_records(domain: str, timeout: float) -> Answer:
    'Return the DNS response for checking, optionally raise exceptions.'
    try:
        return resolve(
            qname=domain, rdtype=rdtype_mx, lifetime=timeout,
            search=True)
    except NXDOMAIN:
        raise DomainNotFoundError
    except NoNameservers:
        raise NoNameserverError
    except Timeout:
        raise DNSTimeoutError
    except YXDOMAIN:
        raise DNSConfigurationError
    except NoAnswer:
        raise NoMXError


def _get_cleaned_mx_records(domain: str, timeout: float) -> list:
    """
    Return a list of hostnames in the MX record, raise an exception on
    any issues.
    """
    answer = _get_mx_records(domain=domain, timeout=timeout)
    to_check = list()
    host_set = set()
    for record in answer.rrset.processing_order():  # type: MX
        dns_str = record.exchange.to_text().rstrip('.')  # type: str
        if dns_str in host_set:
            continue
        to_check.append(dns_str)
        host_set.add(dns_str)
    result = [x for x in to_check if HOST_REGEX.search(string=x)]
    if not result:
        raise NoValidMXError
    return result


def dns_check(email_address: EmailAddress, timeout: float = 10) -> list:
    """
    Check whether there are any responsible SMTP servers for the email
    address by looking up the DNS MX records.

    In case no responsible SMTP servers can be determined, a variety of
    exceptions is raised depending on the exact issue, all derived from
    `MXError`. Otherwise, return the list of MX hostnames.
    """
    if email_address.domain_literal_ip:
        return [email_address.domain_literal_ip]
    else:
        return _get_cleaned_mx_records(
            domain=email_address.domain, timeout=timeout)
