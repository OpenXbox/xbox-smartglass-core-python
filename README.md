# Xbox-Smartglass-Core

[![PyPi version](https://pypip.in/version/xbox-smartglass-core/badge.svg)](https://pypi.python.org/pypi/xbox-smartglass-core)
[![Docs](https://readthedocs.org/projects/xbox-smartglass-core-python/badge/?version=latest)](http://xbox-smartglass-core-python.readthedocs.io/en/latest/?badge=latest)
[![Build status](https://img.shields.io/github/workflow/status/OpenXbox/xbox-smartglass-core-python/build?label=build)](https://github.com/OpenXbox/xbox-smartglass-core-python/actions?query=workflow%3Abuild)
[![Discord chat](https://img.shields.io/discord/338946086775554048)](https://openxbox.org/discord)

This library provides the core foundation for the smartglass protocol that is used
with the Xbox One Gaming console

For in-depth information, check out the documentation: <https://openxbox.org/smartglass-documentation>

**NOTE: Since 29.02.2020 the following modules are integrated into core: stump, auxiliary, rest-server**
**NOTE: Nano module is still offered seperately**

## Features

* Power on / off the console
* Get system info (running App/Game/Title, dashboard version)
* Media player control (seeing content id, content app, playback actions etc.)
* Stump protocol (Live-TV Streaming / IR control)
* Title / Auxiliary stream protocol (f.e. Fallout 4 companion app)
* Trigger GameDVR remotely
* REST Server

## Frameworks used

* construct - Binary parsing <https://construct.readthedocs.io/>
* cryptography - cryptography magic <https://cryptography.io/en/stable/>
* dpkt - pcap parsing <https://dpkt.readthedocs.io/en/latest/>
* Quart - REST API <https://pypi.org/project/quart/>

## Install

Via pip

```text
pip install xbox-smartglass-core
```

See the end of this README for development-targeted instructions.

## How to use

There are several command line utilities to check out::

```text
xbox-cli
```

Some functionality, such as GameDVR record, requires authentication
with your Microsoft Account to validate you have the right to trigger
such action.

To authenticate / get authentication tokens use::

```text
xbox-authenticate

# Alternative: Use the ncurses terminal ui, it has authentication integrated
xbox-tui
```

## REST Server

Start the REST server

```text
xbox-rest-server
```

For more information consult <https://github.com/OpenXbox/xbox-smartglass-core-python/blob/master/REST_FAQ.md>

## Fallout 4 relay service

To forward the title communication from the Xbox to your local host
to use third-party Fallout 4 Pip boy applications or extensions

```text
xbox-fo4-relay
```

## Screenshots

Here you can see the SmartGlass TUI (Text user interface):

![TUI list](https://raw.githubusercontent.com/OpenXbox/xbox-smartglass-core-python/master/assets/xbox_tui_list.png)
![TUI console](https://raw.githubusercontent.com/OpenXbox/xbox-smartglass-core-python/master/assets/xbox_tui_console.png)
![TUI log](https://raw.githubusercontent.com/OpenXbox/xbox-smartglass-core-python/master/assets/xbox_tui_log.png)
![TUI log detail](https://raw.githubusercontent.com/OpenXbox/xbox-smartglass-core-python/master/assets/xbox_tui_logdetail.png)

## Development workflow

Ready to contribute? Here's how to set up `xbox-smartglass-core-python` for local development.

1. Fork the `xbox-smartglass-core-python` repo on GitHub.
2. Clone your fork locally

```text
git clone git@github.com:your_name_here/xbox-smartglass-core-python.git
```

3. Install your local copy into a virtual environment. This is how you set up your fork for local development

```text
python -m venv ~/pyvenv/xbox-smartglass
source ~/pyvenv/xbox-smartglass/bin/activate
cd xbox-smartglass-core-python
pip install -e .[dev]
```

5. Create a branch for local development::

```text
git checkout -b name-of-your-bugfix-or-feature
```

6. Make your changes.

7. Before pushing the changes to git, please verify they actually work

```text
pytest
```

8. Commit your changes and push your branch to GitHub::

```text
git commit -m "Your detailed description of your changes."
git push origin name-of-your-bugfix-or-feature
```

9. Submit a pull request through the GitHub website.

### Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. Code includes unit-tests.
2. Added code is properly named and documented.
3. On major changes the README is updated.
4. Run tests / linting locally before pushing to remote.

## Credits

Kudos to [joelday](https://github.com/joelday) for figuring out the AuxiliaryStream / TitleChannel communication first!
You can find the original implementation here: [SmartGlass.CSharp](https://github.com/OpenXbox/Xbox-Smartglass-csharp)

This package uses parts of [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [audreyr/cookiecutter-pypackage project template](https://github.com/audreyr/cookiecutter-pypackage)
