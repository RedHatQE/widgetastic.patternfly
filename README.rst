======================
widgetastic.patternfly
======================

.. image:: https://travis-ci.org/RedHatQE/widgetastic.patternfly.svg?branch=master
    :target: https://travis-ci.org/RedHatQE/widgetastic.patternfly

.. image:: https://coveralls.io/repos/github/RedHatQE/widgetastic.patternfly/badge.svg?branch=master
    :target: https://coveralls.io/github/RedHatQE/widgetastic.patternfly?branch=master

.. image:: https://readthedocs.org/projects/widgetasticpatternfly/badge/?version=latest
    :target: http://widgetasticpatternfly.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://www.quantifiedcode.com/api/v1/project/a13ed499c97547598b1507ae7f5c5f47/badge.svg
  :target: https://www.quantifiedcode.com/app/project/a13ed499c97547598b1507ae7f5c5f47
  :alt: Code issues

Patternfly_ widget library for Widgetastic_.

.. _Patternfly: http://www.patternfly.org
.. _Widgetastic: https://github.com/RedHatQE/widgetastic.core

Written originally by Milan Falesnik (mfalesni@redhat.com, http://www.falesnik.net/) and
other contributors since 2016.

Contributors whose contributions were squashed during the library move in order of their first commit:

- Ievgen Zapolskyi
- Pete Savage
- Dmitry Misharov
- Oleksii Tsuman
- Mike Shriver

Usage
=====

.. code-block:: python

    from widgetastic_patternfly import Button

    class SomeView(View):
        add = Button('Add', classes=[Button.PRIMARY])

Check the ``src/widgetastic_patternfly/__init__.py`` for more documentation.
