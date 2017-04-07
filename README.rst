======================
widgetastic.patternfly
======================

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
