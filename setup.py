from setuptools import setup, find_packages

setup(name='validate_email',
      version = '1.3',
      download_url = 'git@github.com:syrusakbary/validate_email.git',
      py_modules = ('validate_email',),
      author = 'Syrus Akbary',
      author_email = 'me@syrusakbary.com',
      description = 'validate_email verifies if an email address is valid and really exists.',
      install_requires=[
            "pyDNS",
      ],
      long_description=open('README.rst').read(),
      keywords = 'email validation verification mx verify',
      url = 'http://github.com/syrusakbary/validate_email',
      license = 'LGPL',
    )
