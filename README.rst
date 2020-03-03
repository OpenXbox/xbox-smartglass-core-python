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
* Trigger GameDVR remotely
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

Via pip::

    pip install xbox-smartglass-core

See the end of this README for development-targeted instructions.

How to use
----------
There are several command line utilities to check out::

    $ xbox-cli

Some functionality, such as GameDVR record, requires authentication
with your Microsoft Account to validate you have the right to trigger
such action.

To authenticate / get authentication tokens use::

    $ xbox-authenticate

    # Alternative: Use the ncurses terminal ui, it has authentication integrated
    $ xbox-tui

REST Server
-----------

Start the REST server::

    $ xbox-rest-server

For more information consult RestFAQ_


Fallout 4 relay service
-----------------------

To forward the title communication from the Xbox to your local host
to use third-party Fallout 4 Pip boy applications or extensions::

    xbox-fo4-relay

Screenshots
-----------
Here you can see the SmartGlass TUI (Text user interface):

.. image:: https://raw.githubusercontent.com/OpenXbox/xbox-smartglass-core-python/master/assets/xbox_tui_list.png

.. image:: https://raw.githubusercontent.com/OpenXbox/xbox-smartglass-core-python/master/assets/xbox_tui_console.png

.. image:: https://raw.githubusercontent.com/OpenXbox/xbox-smartglass-core-python/master/assets/xbox_tui_log.png

.. image:: https://raw.githubusercontent.com/OpenXbox/xbox-smartglass-core-python/master/assets/xbox_tui_logdetail.png


Install for development
-----------------------

Ready to contribute? Here's how to set up `xbox-smartglass-core-python` for local development.

1. Fork the `xbox-smartglass-core-python` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/xbox-smartglass-core-python.git

3. Install your local copy into a virtual environment. This is how you set up your fork for local development::

    $ python -m venv ~/pyvenv/xbox-smartglass
    $ source ~/pyvenv/xbox-smartglass/bin/activate
    $ cd xbox-smartglass-core-python
    $ pip install -e .[dev]

4. Setup git hooks via `pre-commit`. This ensures your code is properly linted and tests are run::

    $ pre-commit install && pre-commit install -t pre-push

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

6. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.
3. The pull request should work for Python 3.6, 3.7 and 3.8. Check
   https://travis-ci.org/OpenXbox/xbox-smartglass-core-python/pull_requests
   and make sure that the tests pass for all supported Python versions.


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
