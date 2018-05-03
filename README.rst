====================
Xbox-Smartglass-Core
====================

.. image:: https://pypip.in/version/xbox-smartglass-core/badge.svg
    :target: https://pypi.python.org/pypi/xbox-smartglass-core/
    :alt: Latest Version

.. image:: https://readthedocs.org/projects/xbox-smartglass-core-python/badge/?version=latest
    :target: http://xbox-smartglass-core-python.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://travis-ci.org/OpenXbox/xbox-smartglass-core-python.svg?branch=master
    :target: https://travis-ci.org/OpenXbox/xbox-smartglass-core-python

This library provides the core foundation for the smartglass protocol that is used
with the Xbox One Gaming console

For in-depth information, check out the documentation: (https://openxbox.github.io)

Dependencies
------------
* Python >= 3.5
* construct (https://construct.readthedocs.io/)
* cryptography (https://cryptography.io/en/stable/)
* gevent (http://www.gevent.org/)
* dpkt (https://dpkt.readthedocs.io/en/latest/)

How to use
----------

Install::

  pip install xbox-smartglass-core

Usage::

  # client and poweroff scripts need xbox live tokens to function
  # -> authenticate first
  xbox-authenticate
  # alternatively: ncurses terminal ui
  xbox-auth-tui

  # Console Discovery
  xbox-discover

  # Console Poweron (console Live-ID: FD0001232435)
  xbox-poweron FD0001232435

  # Basic Client
  xbox-client

  # Gamepad input (via keyboard)
  xbox-input

  # Text Input
  xbox-text

  # Console Poweroff
  xbox-poweroff --liveid FD0001232435
  or
  xbox-poweroff --address 192.168.0.220
  or
  xbox-poweroff --all

  # PCAP Analyzer - Needs shared secret hexstring to decrypt
  xbox-pcap filename.pcap 0001020304AABBCC..BE

Known issues
------------
* Find, report and/or fix them ;)

Contribute
----------
* Report bugs/suggest features
* Add/update docs
* Enhance managers

Credits
-------
This package uses parts of Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
