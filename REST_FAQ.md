# FAQ - Frequently asked questions

## All `/device/<LIVEID>` endpoints, except `poweron`, reports *Console info ... not available*
You need to discover/refresh available consoles first by calling `/device` endpoint.

## Connect command `/device/<LIVEID>/connect` loads forever/does not succeed
Throubleshoot like this:
1. Call `/auth` endpoint and check **authenticated** boolean value, if it's **false** call `/auth/refresh`.
  If refreshing tokens fails, logout (`/auth/logout`) and login (`/auth/login` or `/auth/oauth`) again.
2. Refresh / rescan available consoles by calling `/device` endpoint.
3. If connection still fails, power-cycle the console. Press the power button on the console front for 10 seconds
  to shut it down entirely. Press the power button again and wait for it to fully boot.
4. Try to connect again.
