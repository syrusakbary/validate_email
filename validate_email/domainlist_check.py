from typing import Optional

from .updater import BLACKLIST_FILE_PATH, BlacklistUpdater

SetOrNone = Optional[set]

# Start an optional update on module load
blacklist_updater = BlacklistUpdater()
blacklist_updater.process(force=False)


class DomainListValidator(object):
    'Check the provided email against domain lists.'
    domain_whitelist = set()
    domain_blacklist = set('localhost')

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
        try:
            with open(BLACKLIST_FILE_PATH) as fd:
                lines = fd.readlines()
        except FileNotFoundError:
            return
        self.domain_blacklist.update(
            x.strip().lower() for x in lines if x.strip())

    def __call__(self, user_part: str, domain_part: str) -> bool:
        'Do the checking here.'
        if domain_part in self.domain_whitelist:
            return True
        if domain_part in self.domain_blacklist:
            return False
        return True


domainlist_check = DomainListValidator()
