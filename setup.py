from setuptools import setup, find_packages

setup(name='validate_email',
      version = '1.2',
      download_url = 'git@github.com:syrusakbary/validate_email.git',
      py_modules = ('validate_email',),
      author = 'Syrus Akbary',
      author_email = 'me@syrusakbary.com',
      description = 'Validate_email verify if an email address is valid and really exists.',
      long_description=open('README.rst').read(),
      keywords = 'email validation verification mx verify',
      url = 'http://github.com/syrusakbary/validate_email',
      license = 'LGPLv3',
      classifiers=('Topic :: Communications :: Email',
                   'Topic :: Utilities',
                   'License :: OSI Approved',
                   'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
                   'Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 3', ))
