from pathlib import Path
from subprocess import check_output
from unittest.case import TestCase

try:
    # OSX Homebrew fix: https://stackoverflow.com/a/53190037/1067833
    from sys import _base_executable as executable
except ImportError:
    from sys import executable


class InstallTest(TestCase):
    'Testing package installation.'

    def test_datadir_is_in_place(self):
        'Data directory should be in the virtualenv.'
        output = check_output([
            executable, '-c', (
                'import sys;sys.path.remove("");import validate_email;'
                'print(validate_email.updater.BLACKLIST_FILEPATH_INSTALLED);'
                'print(validate_email.updater.ETAG_FILEPATH_INSTALLED, end="")'
            )]).decode('ascii')
        bl_path, etag_path = output.split('\n')
        self.assertTrue(
            expr=Path(bl_path).exists(), msg=f'{bl_path!r} doesn\'t exist.')
        self.assertTrue(
            expr=Path(etag_path).exists(),
            msg=f'{etag_path!r} doesn\'t exist.')
