from http.client import HTTPResponse
from logging import getLogger
from pathlib import Path
from tempfile import gettempdir, gettempprefix
from threading import Thread
from time import time
from typing import Callable, Optional
from urllib.error import HTTPError
from urllib.request import Request, urlopen

try:
    from os import geteuid
except ImportError:
    def geteuid():
        'Windows does not have `os.geteuid()`.'
        return '1'


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

    def _read_etag(self) -> Optional[str]:
        'Read the etag header from the stored etag file when exists.'
        for path in [ETAG_FILEPATH_TMP, ETAG_FILEPATH_INSTALLED]:
            try:
                return path.read_text().strip()
            except FileNotFoundError:
                pass

    @property
    def _is_old(self) -> bool:
        'Return `True` if the locally stored file is old.'
        true_when_older_than = time() - self._refresh_when_older_than
        for path in [BLACKLIST_FILEPATH_TMP, BLACKLIST_FILEPATH_INSTALLED]:
            try:
                return path.stat().st_ctime < true_when_older_than
            except FileNotFoundError:
                pass
        return True  # no file found at all

    def _get_headers(self, force_update: bool = False) -> dict:
        'Compile a header with etag if available.'
        headers = dict()
        if force_update:
            return headers
        etag = self._read_etag()
        if not etag:
            return headers
        headers['If-None-Match'] = etag
        return headers

    def _download(self, headers: dict, blacklist_path: Path, etag_path: Path):
        'Downlad and store blacklist file.'
        LOGGER.debug(msg=f'Checking {BLACKLIST_URL}')
        request = Request(url=BLACKLIST_URL, headers=headers)
        response = urlopen(url=request)  # type: HTTPResponse
        # New data available
        LOGGER.debug(msg=f'Writing response into {blacklist_path}')
        blacklist_path.write_bytes(response.fp.read())
        if 'ETag' in response.headers:
            LOGGER.debug(msg=f'Storing ETag response into {etag_path}.')
            etag_path.write_text(response.headers['ETag'])

    def _install(self):
        """
        Download and store the blacklist file and the matching etag file
        into the library path. This is executed from setup.py upon
        installation of the library. Don't call this in your
        application.
        """
        LIB_PATH_DEFAULT.mkdir(exist_ok=True)
        self._download(
                headers={}, blacklist_path=BLACKLIST_FILEPATH_INSTALLED,
                etag_path=ETAG_FILEPATH_INSTALLED)

    def _process(self, force: bool = False):
        'Start optionally updating the blacklist.txt file, while locked.'
        if not force and not self._is_old:
            LOGGER.debug(msg='Not updating because file is fresh enough.')
            return
        try:
            self._download(
                headers=self._get_headers(force_update=force),
                blacklist_path=BLACKLIST_FILEPATH_TMP,
                etag_path=ETAG_FILEPATH_TMP)
        except HTTPError as exc:
            if exc.code == 304:
                # Not modified, update date on the tmp file
                LOGGER.debug(msg='Local file is fresh enough (same ETag).')
                BLACKLIST_FILEPATH_TMP.touch()
                return
            raise

    def process(
            self, force: bool = False, callback: Optional[Callable] = None):
        'Start optionally updating the blacklist.txt file.'
        # Locking to avoid multi-process update on multi-process startup
        # Import filelock locally because this module is als used by setup.py
        from filelock import FileLock
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
    LOGGER.info(msg='Starting optional update of built-in blacklist.')
    blacklist_updater = BlacklistUpdater()
    kwargs = dict(force=force, callback=callback)
    if not background:
        blacklist_updater.process(**kwargs)
        return
    bl_thread = Thread(target=blacklist_updater.process, kwargs=kwargs)
    bl_thread.start()
    return bl_thread
