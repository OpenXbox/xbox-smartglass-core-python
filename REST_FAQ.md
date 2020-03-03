# Xbox Smartglass REST server

## Start the server daemon

Usage information

```bash
usage: xbox-rest-server rest [-h] [--logfile LOGFILE] [-v] [--tokens TOKENS] [--refresh] [--bind BIND] [--port PORT]

optional arguments:
  -h, --help            show this help message and exit
  --logfile LOGFILE     Path for logfile
  -v, --verbose         Set logging level ( -v: INFO, -vv: DEBUG, -vvv: DEBUG_INCL_PACKETS)
  --tokens TOKENS, -t TOKENS
                        Tokenfile to load
  --refresh, -r         Refresh xbox live tokens in provided token file
  --bind BIND, -b BIND  Interface address to bind the server
  --port PORT, -p PORT  Port to bind to, defaults: (REST: 5557, REPL: 5558)
```


Example localhost:

```sh
# Serve the on '127.0.0.1:5557'
$ xbox-rest-server
```

Example local network:

 __192.168.0.100__ is the IP address of your computer running the server:

```sh
$ xbox-rest-server --bind 192.168.0.100 -p 1234
```


## REST API

### Authentication with Xbox Live

Note: 2FA stands for Two Factor Authentication.


#### Authenticate from scratch via graphical webinterface and Microsoft Account email/password.

```
#For non-2FA enabled account
GET http://<REST_SERVER_IP:PORT>/auth/login

#For 2FA enabled account
GET http://<REST_SERVER_IP:PORT>/auth/oauth
```

#### 2FA OAuth via POST request

```
# Get authorize url
GET http://<REST_SERVER_IP:PORT>/auth/url HTTP/1.1
Response-Parameters (JSON): authorization_url
```

```
# Submit redirect url
POST http://<REST_SERVER_IP:PORT>/auth/oauth
Request-Parameters: redirect_uri
```

#### Regular (non-2FA) login via POST request

```
POST http://<REST_SERVER_IP:PORT>/auth/login
Request-Parameters: email, password
```

#### Load/Save tokens from disk, from the filepath provided via `--tokens`

```
# Load from disk
GET http://<REST_SERVER_IP:PORT>/auth/load

# Attempt to refresh online
GET http://<REST_SERVER_IP:PORT>/auth/refresh

# Store updated/refreshed version
GET http://<REST_SERVER_IP:PORT>/auth/store
```


### Console interaction

#### See all API endpoints

```
GET http://<REST_SERVER_IP:PORT>/
```

Response

```json
{
    "endpoints": [
        "/",
        "/auth",
        "/auth/load",
        "/auth/login",
        "/auth/logout",
        "/auth/oauth",
        "/auth/refresh",
        "/auth/store",
        "/auth/url",
        "/device",
        "/device/<liveid>",
        "/device/<liveid>/connect",
        "/device/<liveid>/console_status",
        "/device/<liveid>/disconnect",
        "/device/<liveid>/gamedvr",
        "/device/<liveid>/input",
        "/device/<liveid>/input/<button>",
        "/device/<liveid>/ir",
        "/device/<liveid>/ir/<device_id>",
        "/device/<liveid>/ir/<device_id>/<button>",
        "/device/<liveid>/launch/<path:app_id>",
        "/device/<liveid>/media",
        "/device/<liveid>/media/<command>",
        "/device/<liveid>/media/seek/<int:seek_position>",
        "/device/<liveid>/media_status",
        "/device/<liveid>/nano",
        "/device/<liveid>/nano/start",
        "/device/<liveid>/nano/stop",
        "/device/<liveid>/poweroff",
        "/device/<liveid>/poweron",
        "/device/<liveid>/stump/headend",
        "/device/<liveid>/stump/livetv",
        "/device/<liveid>/stump/tuner_lineups",
        "/device/<liveid>/text",
        "/device/<liveid>/text/<text>",
        "/static/<path:filename>",
        "/versions",
        "/web/pins",
        "/web/title/<title_id>",
        "/web/titlehistory"
    ],
    "success": true
}
```

#### Power on console

Request

```
GET http://<REST_SERVER_IP:PORT>/device/<liveid>/poweron

# NOTE: You can specify device by ip via query parameter `addr`
GET http://<REST_SERVER_IP:PORT>/device/<liveid>/poweron?addr=192.168.0.123
```

Response

```json
{"success":true}
```

#### Enumerate active (aka. powered on) devices on the network

Request

```
GET http://<REST_SERVER_IP:PORT>/device

# NOTE: You can enumerate device by ip via query parameter `addr`
GET http://<REST_SERVER_IP:PORT>/device?addr=192.168.0.123
```

Response

```json
{
    "devices": {
        "FD93473625FB3432": {
            "address": "10.0.0.123",
            "anonymous_connection_allowed": true,
            "authenticated_users_allowed": true,
            "connection_state": "Disconnected",
            "console_users_allowed": false,
            "device_status": "Available",
            "is_certificate_pending": false,
            "last_error": 0,
            "liveid": "FD93473625FB3432",
            "name": "FancyXbox",
            "pairing_state": "NotPaired",
            "uuid": "24db9bd7-1ff9-4351-ae90-f6e1aa5f88a9"
        }
    },
    "success": true
}
```
#### Connect to a console

Request
```
GET http://<REST_SERVER_IP:PORT>/device/<liveid>/connect

# NOTE: You can connect anonymously via query parameter `anonymous`
GET http://<REST_SERVER_IP:PORT>/device/<liveid>/connect/connect?anonymous=true
```

Response

```json
{"connection_state":"Connected","success":true}
```

#### Get console status
Request

```
GET http://<REST_SERVER_IP:PORT>/device/<liveid>/console_status
```

```json
{
    "console_status": {
        "active_titles": [
            {
                "aum": "Xbox.Dashboard_8wekyb3d8bbwe!Xbox.Dashboard.Application",
                "has_focus": false,
                "image": null,
                "name": "Xbox.Dashboard_8wekyb3d8bbwe!Xbox.Dashboard.Application",
                "product_id": "00000000-0000-0000-0000-000000000000",
                "sandbox_id": "00000000-0000-0000-0000-000000000000",
                "title_id": 750323071,
                "title_location": "Full",
                "type": null
            },
            {
                "aum": "Xbox.IdleScreen_8wekyb3d8bbwe!Xbox.IdleScreen.Application",
                "has_focus": true,
                "image": null,
                "name": "Xbox.IdleScreen_8wekyb3d8bbwe!Xbox.IdleScreen.Application",
                "product_id": "00000000-0000-0000-0000-000000000000",
                "sandbox_id": "00000000-0000-0000-0000-000000000000",
                "title_id": 851275400,
                "title_location": "Default",
                "type": null
            }
        ],
        "kernel_version": "10.0.19041",
        "live_tv_provider": 0,
        "locale": "de-DE"
    },
    "success": true
}
```

#### Send gamepad input (only works in dashboard / apps)

Request

```
GET http://localhost:5557/device/<liveid>/input
```

Response

```
{
    "buttons": [
        "clear",
        "enroll",
        "nexus",
        "menu",
        "view",
        "a",
        "b",
        "x",
        "y",
        "dpad_up",
        "dpad_down",
        "dpad_left",
        "dpad_right",
        "left_shoulder",
        "right_shoulder",
        "left_thumbstick",
        "right_thumbstick"
    ],
    "success": true
}
```

Example - Press the home button

```
GET http://localhost:5557/device/<liveid>/input/nexus
```

Response

```json
{"success":true}
```

## Problems

### Connect command `/device/<LIVEID>/connect` loads forever/does not succeed

Troubleshoot like this:

1. Call `/auth` endpoint and check **authenticated** boolean value, if it's **false** call `/auth/refresh`.
  If refreshing tokens fails, logout (`/auth/logout`) and login (`/auth/login` or `/auth/oauth`) again.
2. Refresh / rescan available consoles by calling `/device` endpoint.
3. If connection still fails, power-cycle the console. Press the power button on the console front for 10 seconds
  to shut it down entirely. Press the power button again and wait for it to fully boot.
4. Try to connect again.
