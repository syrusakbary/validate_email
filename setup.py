from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install


class PostDevelopCommand(develop):
    'Post-installation for development mode'

    def run(self):
        super().run()
        with open('/tmp/test-develop', 'w') as fd:
            fd.write(str(vars(self)))


class PostInstallCommand(install):
    'Post-installation for installation mode'

    def run(self):
        super().run()
        with open('/tmp/test-install', 'w') as fd:
            fd.write(str(vars(self)))


setup(
    name='py3-validate-email',
    version='0.1',
    py_modules=('validate_email',),
    install_requires=['dnspython'],
    author='László Károlyi',
    author_email='laszlo@karolyi.hu',
    description='Email validator with regex and SMTP checking.',
    long_description=open('README.rst').read(),
    keywords='email validation verification mx verify',
    url='http://github.com/karolyi/py3-validate-email',
    cmdclass=dict(develop=PostDevelopCommand, install=PostInstallCommand),
    license='LGPL',
)
