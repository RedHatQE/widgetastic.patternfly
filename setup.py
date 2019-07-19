# -*- coding: utf-8 -*-
import codecs
from setuptools import find_packages, setup


setup(
    name="widgetastic.patternfly",
    use_scm_version=True,
    author="Milan Falesnik",
    author_email="mfalesni@redhat.com",
    description='Patternfly widget library for Widgetastic',
    long_description=codecs.open('README.rst', mode='r', encoding='utf-8').read(),
    license="Apache license",
    url="https://github.com/RedHatQE/widgetastic.patternfly",
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
    ],
)
