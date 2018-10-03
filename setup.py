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
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        'widgetastic.core>=0.10.0',
        'aenum==2.1.2'
    ],
    setup_requires=[
        'setuptools_scm',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
    ],
)
