from setuptools import setup, find_packages

setup(name='validate_email',
      version = '1.3',
      download_url = 'git@github.com:syrusakbary/validate_email.git',
      py_modules = ('validate_email',),
      author = 'Syrus Akbary',
      author_email = 'me@syrusakbary.com',
      description = 'validate_email verifies if an email address is valid and really exists.',
      long_description=open('README.rst').read(),
      keywords = 'email validation verification mx verify',
      url = 'http://github.com/syrusakbary/validate_email',
      extras_require = {
            'dns:sys_platform != "win32"': ['pyDNS']
      },
      license = 'LGPL',
    )
