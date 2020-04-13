from logging import getLogger
from typing import Optional

from filelock import FileLock

from .email_address import EmailAddress
from .exceptions import DomainBlacklistedError
from .updater import (
    BLACKLIST_FILEPATH_INSTALLED, BLACKLIST_FILEPATH_TMP, LOCK_PATH,
    update_builtin_blacklist)

SetOrNone = Optional[set]
LOGGER = getLogger(__name__)


class DomainListValidator(object):
    'Check the provided email against domain lists.'
    domain_whitelist = set()
    domain_blacklist = set('localhost')
    _is_builtin_bl_used: bool = False

    def __init__(
            self, whitelist: SetOrNone = None, blacklist: SetOrNone = None):
        if whitelist:
            self.domain_whitelist = set(x.lower() for x in whitelist)
        if blacklist:
            self.domain_blacklist = set(x.lower() for x in blacklist)
        else:
            self._is_builtin_bl_used = True
            self.reload_builtin_blacklist()

    @property
    def _blacklist_path(self) -> str:
        'Return the path of the `blacklist.txt` that should be loaded.'
        try:
            # Zero size: file is touched to indicate the preinstalled
            # file is still fresh enough
            return BLACKLIST_FILEPATH_INSTALLED \
                if BLACKLIST_FILEPATH_TMP.stat().st_size == 0 \
                else BLACKLIST_FILEPATH_TMP
        except FileNotFoundError:
            return BLACKLIST_FILEPATH_INSTALLED

    def reload_builtin_blacklist(self):
        '(Re)load our built-in blacklist.'
        if not self._is_builtin_bl_used:
            return
        with FileLock(lock_file=LOCK_PATH):
            bl_path = self._blacklist_path
            LOGGER.debug(msg=f'(Re)loading blacklist from {bl_path}')
            try:
                with open(bl_path) as fd:
                    lines = fd.readlines()
            except FileNotFoundError:
                return
        self.domain_blacklist = set(
            x.strip().lower() for x in lines if x.strip())

    def __call__(self, address: EmailAddress) -> bool:
        'Do the checking here.'
        if address.domain in self.domain_whitelist:
            return True
        if address.domain in self.domain_blacklist:
            raise DomainBlacklistedError
        return True


domainlist_check = DomainListValidator()
# Start an optional update on module load
update_builtin_blacklist(
    force=False, background=True,
    callback=domainlist_check.reload_builtin_blacklist)
