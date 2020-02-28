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

.. image:: https://img.shields.io/badge/discord-OpenXbox-blue.svg
    :target: https://discord.gg/E8kkJhQ
    :alt: Discord chat channel

This library provides the core foundation for the smartglass protocol that is used
with the Xbox One Gaming console

For in-depth information, check out the documentation: (https://openxbox.github.io)

Features
--------
* Power on / off the console
* Get system info (running App/Game/Title, dashboard version)
* Media player control (seeing content id, content app, playback actions etc.)
* Title / Auxiliary stream protocol (f.e. Fallout 4 companion app)

Dependencies
------------
* Python >= 3.5
* construct (https://construct.readthedocs.io/)
* cryptography (https://cryptography.io/en/stable/)
* gevent (http://www.gevent.org/)
* dpkt (https://dpkt.readthedocs.io/en/latest/)

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

Now have a look in the Documentation_ how to use the provided shell-scripts!

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