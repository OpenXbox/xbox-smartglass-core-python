# CHANGELOG

## 1.3.0 (2020-11-02)

* Drop Python 3.6 support
* Deprecate Authentication via TUI
* Major rewrite (Migration from gevent -> asyncio)
* Rewrite of REST Server (Migration FLASK -> FastAPI)
* Adjust to xbox-webapi-python v2.0.8
* New OAUTH login flow

## 1.2.2  (2020-04-03)

* Fix: Assign tokenfile path to flask_app (aka. REST server instance)

## 1.2.1  (2020-03-04)

* cli: Python3.6 compatibility change
* HOTFIX: Add xbox.handlers to packages in setup.py

## 1.2.0  (2020-03-04)

* CLI scripts rewritten, supporting log/loglevel args now, main script is called xbox-cli now
* Add REPL / REPL server functionality
* Updates to README and REST server documentation

## 1.1.2  (2020-02-29)

* Drop support for Python 3.5
* crypto: Fix deprecated cryptography functions
* tests: Speed up REST server tests (discovery, poweron)
* Update all dependencies

## 1.1.1  (2020-02-29)

* FIX: Include static files for REST server in distributable package
* REST: Remove deprecated packages from showing in /versions endpoint

## 1.1.0  (2020-02-29)

* Clean up dependencies
* Merge in **xbox-smartglass-rest**, deprecate standalone package
* Merge in **xbox-smartglass-stump**, deprecate standalone package
* Merge in **xbox-smartglass-auxiliary**, deprecate standalone package
* tui: Fix crash when bringing up command menu, support ESC to exit

## 1.0.12 (2018-11-14)

* Python 3.7 compatibility

## 1.0.11 (2018-11-05)

* Add game_dvr_record to Console-class
* Fix PCAP parser
* Add last_error property to Console-class

## 1.0.10 (2018-08-14)

* Safeguard around connect() functions, if userhash and xsts_token is NoneType

## 1.0.9 (2018-08-11)

* Fix for Console instance poweron
* Reset state after poweroff
* Little fixes to TUI
* Support handling MessageFragments

## 1.0.8 (2018-06-14)

* Use aenum library for backwards-compat with _enum.Flag_ on py3.5

## 1.0.7 (2018-05-16)

* CoreProtocol.connect: Treat ConnectionResult.Pending as error
* constants.WindowsClientInfo: Update ClientVersion 15 -> 39
* Make CoreProtocol.start_channel take optional title_id / activity_id arguments

## 1.0.1 (2018-05-03)

* First release on PyPI.
