from datetime import datetime
from ipaddress import IPv4Address, IPv6Address, ip_address
from logging import getLogger
from socket import has_ipv6
from typing import FrozenSet, List, Type, Union

from dns.exception import DNSException, Timeout
from dns.rdataclass import IN as rdcl_in
from dns.rdatatype import AAAA as rdtype_aaaa
from dns.rdatatype import MX as rdtype_mx
from dns.rdatatype import A as rdtype_a
from dns.rdtypes.ANY.MX import MX as restype_mx
from dns.resolver import (
    NXDOMAIN, YXDOMAIN, Answer, NoAnswer, NoNameservers, resolve)
from typing_extensions import Literal

from .constants import HOST_REGEX
from .email_address import EmailAddress
from .exceptions import (
    DNSConfigurationError, DNSTimeoutError, DomainNotFoundError, NoMXError,
    NoNameserverError, NoValidMXError)

LOGGER = getLogger(name=__name__)
AddressTypes = FrozenSet[Union[Type[IPv4Address], Type[IPv6Address]]]
DefaultAddressTypes = frozenset([IPv4Address, IPv6Address])


def _get_mx_records(domain: str, timeout: float) -> Answer:
    'Return the DNS response for checking, optionally raise exceptions.'
    try:
        return resolve(
            qname=domain, rdtype=rdtype_mx, lifetime=timeout, search=True)
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


def _resolve_one_recordtype(
        hostname: str, records: List[str], timeout: float,
        rdtype: Literal[rdtype_aaaa, rdtype_a], result_set: set) -> float:
    """
    Resolve one recordtype, add to results, return the new timeout
    value.
    """
    if timeout <= 0:
        return 0
    time_current = datetime.now()
    try:
        query_result = resolve(
            qname=hostname, rdtype=rdtype, rdclass=rdcl_in, lifetime=timeout)
        for item in query_result.rrset.processing_order():
            text: str = item.to_text()
            if text in result_set:
                LOGGER.debug(msg=(
                    f'{hostname} resolved to {text!r} already in results,'
                    ' not adding'))
                continue
            records.append(text)
            result_set.add(text)
            LOGGER.debug(msg=f'{hostname} resolved to {text}')
    except DNSException as exc:
        LOGGER.warning(msg=f'{hostname} resolve error: {exc}')
    return timeout - (datetime.now() - time_current).total_seconds()


def _get_resolved_mx_records(
    records: list, timeout: float,
    address_types: AddressTypes = DefaultAddressTypes
) -> List[str]:
    'Return a resolved & sorted list of IP addresses from MX records.'
    result = []
    result_set = set()
    for record in records:
        if timeout <= 0:
            break
        if IPv6Address in address_types and has_ipv6:
            timeout = _resolve_one_recordtype(
                hostname=record, records=result, timeout=timeout,
                rdtype=rdtype_aaaa, result_set=result_set)
        if IPv4Address in address_types:
            timeout = _resolve_one_recordtype(
                hostname=record, records=result, timeout=timeout,
                rdtype=rdtype_a, result_set=result_set)
    return result


def _get_cleaned_mx_records(
    domain: str, timeout: float,
    address_types: AddressTypes = DefaultAddressTypes
) -> List[str]:
    """
    Return a list of hostnames in the MX record, raise an exception on
    any issues.
    """
    time_start = datetime.now()
    answer = _get_mx_records(domain=domain, timeout=timeout)
    to_check = list()
    host_set = set()
    record: restype_mx
    for record in answer.rrset.processing_order():
        dns_str = record.exchange.to_text().rstrip('.')  # type: str
        if dns_str in host_set:
            LOGGER.debug(msg=f'{dns_str} is already in results, not adding')
            continue
        to_check.append(dns_str)
        host_set.add(dns_str)
    result = [x for x in to_check if HOST_REGEX.search(string=x)]
    LOGGER.debug(msg=f'{domain} resolved (MX): {result}')
    if not result:
        raise NoValidMXError
    time_diff = timeout - (datetime.now() - time_start).total_seconds()
    result = _get_resolved_mx_records(
        records=result, timeout=time_diff, address_types=address_types)
    return result


def dns_check(
        email_address: EmailAddress, timeout: float = 10,
        address_types: AddressTypes = DefaultAddressTypes) -> List[str]:
    """
    Check whether there are any responsible SMTP servers for the email
    address by looking up the DNS MX records.

    In case no responsible SMTP servers can be determined, a variety of
    exceptions is raised depending on the exact issue, all derived from
    `MXError`. Otherwise, return the list of MX hostnames.
    """
    if email_address.domain_literal_ip:
        ip = ip_address(address=email_address.domain_literal_ip)
        if type(ip) not in address_types:
            raise NoValidMXError
        return [email_address.domain_literal_ip]
    else:
        return _get_cleaned_mx_records(
            domain=email_address.domain, timeout=timeout,
            address_types=address_types)
