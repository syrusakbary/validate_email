from setuptools import find_packages, setup

setup(
    name='py3-validate-email',
    version='0.6',
    py_modules=('validate_email',),
    install_requires=['dnspython'],
    author='László Károlyi',
    author_email='laszlo@karolyi.hu',
    description='Email validator with regex and SMTP checking.',
    long_description=open('README.rst').read(),
    keywords='email validation verification mx verify',
    url='http://github.com/karolyi/py3-validate-email',
    download_url=(
        'http://github.com/karolyi/py3-validate-email/archive/0.1.tar.gz'),
    license='LGPL',
)
