from http.client import HTTPResponse
from os import makedirs
from pathlib import Path
from time import time
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BLACKLIST_URL = (
    'https://raw.githubusercontent.com/martenson/disposable-email-domains/'
    'master/disposable_email_blocklist.conf')
LIB_PATH = Path(__file__).resolve().parent.joinpath('lib')
BLACKLIST_FILE_PATH = LIB_PATH.joinpath('blacklist.txt')


class BlacklistUpdater(object):
    'Optionally auto-update the built-in `blacklist.txt`.'

    _etag_file_path = LIB_PATH.joinpath('blacklist_etag.txt')
    _refresh_when_older_than = 5 * 24 * 60 * 60  # 5 days

    def __init__(self):
        makedirs(name=LIB_PATH, exist_ok=True)

    def _read_etag(self) -> Optional[str]:
        'Read the etag header from the stored etag file when exists.'
        try:
            with open(self._etag_file_path) as fd:
                return fd.read().strip()
        except FileNotFoundError:
            pass

    def _write_etag(self, content: str):
        'Write the etag of the newly received file to the cache.'
        with open(self._etag_file_path, 'w') as fd:
            fd.write(content)

    @property
    def is_local_old(self) -> bool:
        'Return `True` if the locally stored file is old.'
        try:
            ctime = BLACKLIST_FILE_PATH.stat().st_ctime
            return ctime < time() - self._refresh_when_older_than
        except FileNotFoundError:
            return True

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

    def _write_new_file(self, response: HTTPResponse):
        'Write new data file on its arrival.'
        if 'ETag' in response.headers:
            self._write_etag(response.headers.get('ETag'))
        with open(BLACKLIST_FILE_PATH, 'wb') as fd:
            fd.write(response.fp.read())

    def process(self, force: bool = False):
        'Start optionally updating the blacklist.txt file.'
        if not force and not self.is_local_old:
            return
        request = Request(
            url=BLACKLIST_URL, headers=self._get_headers(force_update=force))
        try:
            response = urlopen(url=request)  # type: HTTPResponse
            # New data available
            self._write_new_file(response=response)
        except HTTPError as exc:
            if exc.code == 304:
                print('not modified')
                # Not modified, update date on the etag file
                BLACKLIST_FILE_PATH.touch()
