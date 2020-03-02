====================
Xbox-Smartglass-Core
====================

.. image:: https://pypip.in/version/xbox-smartglass-core/badge.svg
    :target: https://pypi.python.org/pypi/xbox-smartglass-core/
    :alt: Latest Version

.. image:: https://readthedocs.org/projects/xbox-smartglass-core-python/badge/?version=latest
    :target: http://xbox-smartglass-core-python.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://travis-ci.com/OpenXbox/xbox-smartglass-core-python.svg?branch=master
    :target: https://travis-ci.com/OpenXbox/xbox-smartglass-core-python

.. image:: https://img.shields.io/docker/build/openxbox/xbox-smartglass-core.svg
    :target: https://hub.docker.com/r/openxbox/xbox-smartglass-core
    :alt: Docker Build Status

.. image:: https://img.shields.io/discord/338946086775554048
    :target: https://openxbox.org/discord
    :alt: Discord chat channel

This library provides the core foundation for the smartglass protocol that is used
with the Xbox One Gaming console

For in-depth information, check out the documentation: (https://openxbox.github.io)

**NOTE: Since 29.02.2020 the following modules are integrated into core: stump, auxiliary, rest-server**

**NOTE: Nano module is still offered seperately**

Features
--------
* Power on / off the console
* Get system info (running App/Game/Title, dashboard version)
* Media player control (seeing content id, content app, playback actions etc.)
* Stump protocol (Live-TV Streaming / IR control)
* Title / Auxiliary stream protocol (f.e. Fallout 4 companion app)
* REST Server

Frameworks used
---------------
* construct - Binary parsing (https://construct.readthedocs.io/)
* cryptography - cryptography magic (https://cryptography.io/en/stable/)
* gevent - coroutines (http://www.gevent.org/)
* dpkt - pcap parsing (https://dpkt.readthedocs.io/en/latest/)
* Flask - REST API (https://pypi.org/project/Flask/)

Install
-------

Via pip:
::

    pip install xbox-smartglass-core


How to use
----------

Authenticate first (Authentication provided by xbox-webapi-python):
::

    $ xbox-authenticate

    # Alternative: Use the ncurses terminal ui, it has authentication integrated
    $ xbox-tui

There are several command line utilities to check out
::

    $ xbox-cli

REST Server
-----------

Start the REST server
::

    $ xbox-rest-server

Incase you run into a problem, check out RestFAQ_

REST Server - Authentication
----------------------------

Authenticate from scratch
::

    For non-2FA enabled account: http://localhost:5557/auth/login
    For 2FA: http://localhost:5557/auth/oauth

    # Store tokens on valid authentication
    http://localhost:5557/auth/store

Load tokens from disk
::

    http://localhost:5557/auth/load
    http://localhost:5557/auth/refresh

2FA OAuth - POST
::

    # Get authorize url
    GET http://localhost:5557/auth/url
    Response-Parameters (JSON): authorization_url

    # Submit redirect url
    POST http://localhost:5557/auth/oauth
    Request-Parameters: redirect_uri

Regular (non-2FA) login - POST
::

    POST http://localhost:5557/auth/login
    Request-Parameters: email, password

REST Server - General usage
---------------------------

To see all API endpoints:
::

    http://localhost:5557


Usual usage:
::

    # (Optional) Poweron console
    http://localhost:5557/device/<liveid>/poweron
    # NOTE: You can specify device by ip: /device/<liveid>/poweron?addr=192.168.0.123
    # Enumerate devices on network
    # NOTE: You can enumerate device by specific ip: /device?addr=192.168.0.123
    http://localhost:5557/device
    # Connect to console
    # NOTE: You can connect anonymously: /connect?anonymous=true
    # .. if console allows it ..
    http://localhost:5557/device/<liveid>/connect

    # Use other API endpoints ...

Fallout 4 relay service
-----------------------

To forward the title communication from the Xbox to your local host
to use third-party Fallout 4 Pip boy applications or extensions:

::

    xbox-fo4-relay


Screenshots
-----------
Here you can see the SmartGlass TUI (Text user interface):

.. image:: https://raw.githubusercontent.com/OpenXbox/xbox-smartglass-core-python/master/assets/xbox_tui_list.png

.. image:: https://raw.githubusercontent.com/OpenXbox/xbox-smartglass-core-python/master/assets/xbox_tui_console.png

.. image:: https://raw.githubusercontent.com/OpenXbox/xbox-smartglass-core-python/master/assets/xbox_tui_log.png

.. image:: https://raw.githubusercontent.com/OpenXbox/xbox-smartglass-core-python/master/assets/xbox_tui_logdetail.png

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
Kudos to joelday_ for figuring out the AuxiliaryStream / TitleChannel communication first!
You can find the original implementation here: SmartGlass.CSharp_.

This package uses parts of Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Documentation: https://xbox-smartglass-core-python.readthedocs.io/en/latest/source/xbox.sg.scripts.html
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
.. _joelday: https://github.com/joelday
.. _SmartGlass.CSharp: https://github.com/OpenXbox/Xbox-Smartglass-csharp
.. _RestFAQ: https://github.com/OpenXbox/xbox-smartglass-core-python/blob/master/REST_FAQ.md
