from os.path import dirname, join
from typing import Optional

SetOrNone = Optional[set]


class DomainListValidator(object):
    'Check the provided email against domain lists.'
    domain_whitelist = frozenset()
    domain_blacklist = frozenset()

    def __init__(
            self, whitelist: SetOrNone = None, blacklist: SetOrNone = None):
        if whitelist:
            self.domain_whitelist = set(x.lower() for x in whitelist)
        if blacklist:
            self.domain_blacklist = set(x.lower() for x in blacklist)
        else:
            self._load_builtin_blacklist()

    def _load_builtin_blacklist(self):
        'Load our built-in blacklist.'
        path = join(dirname(__file__), 'lib', 'blacklist.txt')
        try:
            with open(path) as fd:
                lines = fd.readlines()
        except FileNotFoundError:
            return
        self.domain_blacklist = \
            set(x.strip().lower() for x in lines if x.strip())

    def __call__(self, email_address: str) -> bool:
        'Do the checking here.'
        if not email_address or '@' not in email_address:
            return False

        user_part, domain_part = email_address.rsplit('@', 1)

        if domain_part in self.domain_whitelist:
            return True
        if domain_part in self.domain_blacklist:
            return False
        return True


domainlist_check = DomainListValidator()
