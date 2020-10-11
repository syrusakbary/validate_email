import sys
from distutils import log
from pathlib import Path

from setuptools import find_packages, setup
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop


def run_initial_updater(path: Path):
    'Download an initial blacklist.txt on install time.'
    # Only import the updater module to avoid requiring all the dependencies
    # and auto-running the updater.
    sys.path.append(str(path.joinpath('validate_email')))
    orig_dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        from updater import BLACKLIST_FILEPATH_INSTALLED, BlacklistUpdater
        log.info(f'downloading blacklist to {BLACKLIST_FILEPATH_INSTALLED}')
        BlacklistUpdater()._install()
    finally:
        sys.path = sys.path[:-1]
        sys.dont_write_bytecode = orig_dont_write_bytecode


class DevelopCommand(develop):
    """
    Adapted version of the 'develop' command.

    After finishing the usual build run, download the blacklist and
    store it into the source directory, because that is from where the
    library will run in a developer install.
    """

    def run(self):
        super().run()
        if not self.dry_run:
            run_initial_updater(Path(__file__).parent)


class BuildPyCommand(build_py):
    """
    Adapted version of the 'build_py' command.

    After finishing the usual build run, download the blacklist and
    store it into the build directory. A subsequent 'install' step will
    copy the full contents of the build directory to the install
    target, thus including the blacklist.
    """

    def run(self):
        super().run()
        if not self.dry_run:
            run_initial_updater(Path(self.build_lib))


setup(
    name='py3-validate-email',
    version='0.2.10',
    packages=find_packages(exclude=['tests']),
    install_requires=['dnspython~=2.0', 'idna~=2.10', 'filelock~=3.0'],
    author='László Károlyi',
    author_email='laszlo@karolyi.hu',
    description=(
        'Email validator with regex, blacklisted domains and SMTP checking.'),
    long_description=Path(__file__).parent.joinpath('README.rst').read_text(),
    long_description_content_type='text/x-rst',
    keywords='email validation verification mx verify',
    url='http://github.com/karolyi/py3-validate-email',
    cmdclass=dict(build_py=BuildPyCommand, develop=DevelopCommand),
    license='LGPL',
)
