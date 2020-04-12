from pathlib import Path
from subprocess import check_call

from setuptools import find_packages, setup
from setuptools.command.develop import develop
from setuptools.command.install import install

try:
    # OSX Homebrew fix: https://stackoverflow.com/a/53190037/1067833
    from sys import _base_executable as executable
except ImportError:
    from sys import executable

_DEPENDENCIES = ['dnspython>=1.16.0', 'idna>=2.8', 'filelock>=3.0.12']
with open(Path(__file__).parent.joinpath('README.rst')) as fd:
    _LONG_DESC = fd.read()


class PostInstallCommand(install):
    'Post-installation command.'

    def run(self):
        if self.dry_run:
            return super().run()
        # Install dependencies so the initial update can run
        check_call([executable, '-m', 'pip', 'install'] + _DEPENDENCIES)
        # The updater will walk code stack frames and see if this
        # variable is set in locals() to determine if it is run from the
        # setup, in which case it won't autoupdate.
        _IS_VALIDATEEMAIL_SETUP = True
        from validate_email.updater import BlacklistUpdater
        blacklist_updater = BlacklistUpdater()
        blacklist_updater._is_install_time = _IS_VALIDATEEMAIL_SETUP
        blacklist_updater.process(force=True)
        super().run()


class PostDevelopCommand(develop):
    'Post-installation command.'

    def run(self):
        if self.dry_run:
            return super().run()
        # Install dependencies so the initial update can run
        check_call([executable, '-m', 'pip', 'install'] + _DEPENDENCIES)
        # The updater will walk code stack frames and see if this
        # variable is set in locals() to determine if it is run from the
        # setup, in which case it won't autoupdate.
        _IS_VALIDATEEMAIL_SETUP = True
        from validate_email.updater import BlacklistUpdater
        blacklist_updater = BlacklistUpdater()
        blacklist_updater._is_install_time = _IS_VALIDATEEMAIL_SETUP
        blacklist_updater.process(force=True)
        super().run()


setup(
    name='py3-validate-email',
    version='0.2.1',
    packages=find_packages(exclude=['tests']),
    install_requires=_DEPENDENCIES,
    author='László Károlyi',
    author_email='laszlo@karolyi.hu',
    description=(
        'Email validator with regex, blacklisted domains and SMTP checking.'),
    long_description=_LONG_DESC,
    long_description_content_type='text/x-rst',
    keywords='email validation verification mx verify',
    url='http://github.com/karolyi/py3-validate-email',
    cmdclass=dict(install=PostInstallCommand, develop=PostDevelopCommand),
    license='LGPL',
)
