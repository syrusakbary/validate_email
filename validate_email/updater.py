from http.client import HTTPResponse
from logging import getLogger
from os import geteuid
from pathlib import Path
from tempfile import gettempdir, gettempprefix
from threading import Thread
from time import time
from typing import Callable, Optional
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from filelock import FileLock

from .utils import is_setuptime

LOGGER = getLogger(__name__)
TMP_PATH = Path(gettempdir()).joinpath(
    f'{gettempprefix()}-py3-validate-email-{geteuid()}')
TMP_PATH.mkdir(exist_ok=True)
BLACKLIST_URL = (
    'https://raw.githubusercontent.com/martenson/disposable-email-domains/'
    'master/disposable_email_blocklist.conf')
LIB_PATH_DEFAULT = Path(__file__).resolve().parent.joinpath('data')
BLACKLIST_FILEPATH_INSTALLED = LIB_PATH_DEFAULT.joinpath('blacklist.txt')
BLACKLIST_FILEPATH_TMP = TMP_PATH.joinpath('blacklist.txt')
ETAG_FILEPATH_INSTALLED = LIB_PATH_DEFAULT.joinpath('blacklist.etag.txt')
ETAG_FILEPATH_TMP = TMP_PATH.joinpath('blacklist.etag.txt')
LOCK_PATH = TMP_PATH.joinpath('blacklistupdater.lock')


class BlacklistUpdater(object):
    """
    Optionally auto-update the built-in `blacklist.txt`, while using
    a temporary place to put the newly downloaded one to avoid read-only
    filesystem errors. If the installed `blacklist.txt` is fresh enough
    don't look for newer versions.
    """

    _refresh_when_older_than: int = 5 * 24 * 60 * 60  # 5 days
    _is_install_time: bool = False

    @property
    def _etag_filepath(self) -> str:
        'Return the ETag file path to use.'
        return ETAG_FILEPATH_INSTALLED \
            if self._is_install_time else ETAG_FILEPATH_TMP

    @property
    def _blacklist_filepath(self) -> str:
        'Return the blacklist file path to use.'
        return BLACKLIST_FILEPATH_INSTALLED \
            if self._is_install_time else BLACKLIST_FILEPATH_TMP

    def _read_etag(self) -> Optional[str]:
        'Read the etag header from the stored etag file when exists.'
        for path in [ETAG_FILEPATH_TMP, ETAG_FILEPATH_INSTALLED]:
            try:
                with open(path) as fd:
                    return fd.read().strip()
            except FileNotFoundError:
                pass

    def _write_etag(self, content: str):
        'Write the etag of the newly received file to the cache.'
        path = self._etag_filepath
        LOGGER.debug(msg=f'Storing ETag response into {path}.')
        with open(path, 'w') as fd:
            fd.write(content)

    @property
    def _is_old(self) -> bool:
        'Return `True` if the locally stored file is old.'
        true_when_older_than = time() - self._refresh_when_older_than
        try:
            ctime = BLACKLIST_FILEPATH_TMP.stat().st_ctime
            if ctime >= true_when_older_than:
                # Downloaded tmp file is still fresh enough
                return False
        except FileNotFoundError:
            pass
        try:
            ctime = BLACKLIST_FILEPATH_INSTALLED.stat().st_ctime
        except FileNotFoundError:
            return True
        return ctime < true_when_older_than

    def _get_headers(self, force_update: bool = False) -> dict:
        'Compile a header with etag if available.'
        headers = dict()
        if force_update or self._is_install_time:
            return headers
        etag = self._read_etag()
        if not etag:
            return headers
        headers['If-None-Match'] = etag
        return headers

    def _write_new_file(self, response: HTTPResponse):
        'Write new data file on its arrival.'
        if 'ETag' in response.headers:
            self._write_etag(response.headers.get('ETag'))
        path = self._blacklist_filepath
        LOGGER.debug(msg=f'Writing response into {path}')
        with open(path, 'wb') as fd:
            fd.write(response.fp.read())

    def _process(self, force: bool = False):
        'Start optionally updating the blacklist.txt file, while locked.'
        if not force and not self._is_old:
            LOGGER.debug(msg='Not updating because file is fresh enough.')
            return
        LOGGER.debug(msg=f'Checking {BLACKLIST_URL}')
        request = Request(
            url=BLACKLIST_URL, headers=self._get_headers(force_update=force))
        try:
            response = urlopen(url=request)  # type: HTTPResponse
            # New data available
            self._write_new_file(response=response)
        except HTTPError as exc:
            if exc.code == 304:
                # Not modified, update date on the tmp file
                LOGGER.debug(msg=f'Local file is fresh enough (same ETag).')
                BLACKLIST_FILEPATH_TMP.touch()
                return
            raise

    def process(
            self, force: bool = False, callback: Optional[Callable] = None):
        'Start optionally updating the blacklist.txt file.'
        # Locking to avoid multi-process update on multi-process startup
        with FileLock(lock_file=LOCK_PATH):
            self._process(force=force)
        # Always execute callback because multiple processes can have
        # different versions of blacklists (one before, one after
        # updating)
        if callback:
            callback()


def update_builtin_blacklist(
        force: bool = False, background: bool = True,
        callback: Callable = None) -> Optional[Thread]:
    """
    Update and reload the built-in blacklist. Return the `Thread` used
    to do the background update, so it can be `join()`-ed.
    """
    if is_setuptime():
        return
    LOGGER.info(msg='Starting optional update of built-in blacklist.')
    blacklist_updater = BlacklistUpdater()
    kwargs = dict(force=force, callback=callback)
    if not background:
        blacklist_updater.process(**kwargs)
        return
    bl_thread = Thread(target=blacklist_updater.process, kwargs=kwargs)
    bl_thread.start()
    return bl_thread
