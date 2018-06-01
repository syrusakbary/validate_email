from setuptools import setup, find_packages

setup(
    name="pyemailval",
    version="0.2",
    py_modules=("pyemailval",),
    author="Ben Baert",
    author_email="ben_b@gmx.com",
    description="pyemailval verifies if an email address really exists.",
    long_description=open("README.rst").read(),
    keywords="email validation verification mx verify",
    url="http://github.com/ben-baert/pyemailval",
    download_url="http://github.com/ben-baert/pyemailval/archive/0.1.tar.gz",
    license="LGPL",
)
