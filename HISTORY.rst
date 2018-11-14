=======
History
=======

1.0.12 (2018-11-14)
-------------------

* Python 3.7 compatibility

1.0.11 (2018-11-05)
-------------------

* Add game_dvr_record to Console-class
* Fix PCAP parser
* Add last_error property to Console-class

1.0.10 (2018-08-14)
-------------------

* Safeguard around connect() functions, if userhash and xsts_token is NoneType

1.0.9 (2018-08-11)
------------------
* Fix for Console instance poweron
* Reset state after poweroff
* Little fixes to TUI
* Support handling MessageFragments

1.0.8 (2018-06-14)
------------------
* Use aenum library for backwards-compat with _enum.Flag_ on py3.5

1.0.7 (2018-05-16)
------------------
* CoreProtocol.connect: Treat ConnectionResult.Pending as error
* constants.WindowsClientInfo: Update ClientVersion 15 -> 39
* Make CoreProtocol.start_channel take optional title_id / activity_id arguments

1.0.1 (2018-05-03)
------------------

* First release on PyPI.
