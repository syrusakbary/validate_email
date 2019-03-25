from os.path import join
from urllib.request import urlopen

from setuptools import find_packages, setup
from setuptools.command.build_py import build_py

blacklist_url = (
    'https://raw.githubusercontent.com/martenson/disposable-email-domains/'
    'master/disposable_email_blocklist.conf')


class PostBuildPyCommand(build_py):
    'Post-installation for build_py'

    def run(self):
        if self.dry_run:
            return super().run()
        with urlopen(url=blacklist_url) as fd:
            content = fd.read().decode('utf-8')
        target_dir = join(self.build_lib, 'validate_email/lib')
        self.mkpath(target_dir)
        with open(join(target_dir, 'blacklist.txt'), 'w') as fd:
            fd.write(content)
        super().run()


setup(
    name='py3-validate-email',
    version='0.1.5',
    packages=find_packages(exclude=['tests']),
    install_requires=['dnspython'],
    author='László Károlyi',
    author_email='laszlo@karolyi.hu',
    description='Email validator with regex and SMTP checking.',
    long_description=open('README.rst').read(),
    long_description_content_type='text/x-rst',
    keywords='email validation verification mx verify',
    url='http://github.com/karolyi/py3-validate-email',
    cmdclass=dict(build_py=PostBuildPyCommand),
    license='LGPL',
)
