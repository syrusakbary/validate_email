from logging import getLogger
from pathlib import Path
from typing import Optional

from filelock import FileLock

from .email_address import EmailAddress
from .exceptions import DomainBlacklistedError
from .updater import (
    BLACKLIST_FILEPATH_INSTALLED, BLACKLIST_FILEPATH_TMP, ENV_IGNORE_UPDATER,
    LOCK_PATH, TMP_PATH, update_builtin_blacklist)

SetOrNone = Optional[set]
LOGGER = getLogger(__name__)


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
            self.reload_builtin_blacklist()

    @property
    def _blacklist_path(self) -> Path:
        'Return the path of the `blacklist.txt` that should be loaded.'
        try:
            # Zero size: file is touched to indicate the preinstalled
            # file is still fresh enough
            return BLACKLIST_FILEPATH_INSTALLED \
                if BLACKLIST_FILEPATH_TMP.stat().st_size == 0 \
                else BLACKLIST_FILEPATH_TMP
        except FileNotFoundError:
            return BLACKLIST_FILEPATH_INSTALLED

    def _get_blacklist_lines(self) -> list:
        'Return the lines of blacklist.txt as a list.'
        bl_path = self._blacklist_path
        LOGGER.debug(msg=f'(Re)loading blacklist from {bl_path}')
        try:
            with open(bl_path) as fd:
                return fd.readlines()
        except FileNotFoundError:
            return []

    def reload_builtin_blacklist(self):
        '(Re)load our built-in blacklist.'
        # Locking is only necessary when we might have an updater
        # process running
        if ENV_IGNORE_UPDATER:
            lines = self._get_blacklist_lines()
        else:
            TMP_PATH.mkdir(exist_ok=True)
            with FileLock(lock_file=str(LOCK_PATH)):
                lines = self._get_blacklist_lines()
        self.domain_blacklist = set(
            x.strip().lower() for x in lines if x.strip())

    def __call__(self, email_address: EmailAddress) -> bool:
        """
        Check if the email domain is valid, raise
        `DomainBlacklistedError` if not.
        """
        if email_address.domain in self.domain_whitelist:
            return True
        if email_address.domain in self.domain_blacklist:
            raise DomainBlacklistedError
        return True


domainlist_check = DomainListValidator()
# Start an optional update on module load
update_builtin_blacklist(
    force=False, background=True,
    callback=domainlist_check.reload_builtin_blacklist)
