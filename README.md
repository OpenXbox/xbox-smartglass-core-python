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

## Major frameworks used

* Xbox WebAPI <https://github.com/OpenXbox/xbox-webapi-python>
* construct - Binary parsing <https://construct.readthedocs.io/>
* cryptography - cryptography magic <https://cryptography.io/en/stable/>
* dpkt - pcap parsing <https://dpkt.readthedocs.io/en/latest/>
* FastAPI - REST API <https://github.com/tiangolo/fastapi>
* urwid - TUI app <https://github.com/urwid/urwid>
* pydantic - JSON models <https://github.com/samuelcolvin/pydantic>

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
```

## REST server

### Start the server daemon

Usage information

Example localhost:

```sh
# Serve on '127.0.0.1:5557'
$ xbox-rest-server
INFO:     Started server process [927195]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:5557 (Press CTRL+C to quit)
```

Example local network:

 __192.168.0.100__ is the IP address of your computer running the server:

```sh
xbox-rest-server --host 192.168.0.100 -p 1234
INFO:     Started server process [927195]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://192.168.0.100:1234 (Press CTRL+C to quit)
```

### REST API

Since the migration from Flask framework to FastAPI, there is a nice
OpenAPI documentation available:

<http://{IPAddress}:{port}/docs>

### Authentication

If your server runs on something else than 127.0.0.1:5557 or 127.0.0.1:8080 you
need to register your own OAUTH application on **Azure AD** and supply appropriate
parameters to the login-endpoint of the REST server.

Check out: <https://github.com/OpenXbox/xbox-webapi-python/blob/master/README.md>

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

This package uses parts of [Cookiecutter](https://github.com/audreyr/cookiecutter) and the
[audreyr/cookiecutter-pypackage project template](https://github.com/audreyr/cookiecutter-pypackage)
