import argparse
import uvicorn

REST_DEFAULT_SERVER_PORT=5557

def main():
    parser = argparse.ArgumentParser(description='Xbox REST server')
    parser.add_argument(
        '--host', '-b', default='127.0.0.1',
        help='Interface address to bind the server')
    parser.add_argument(
        '--port', '-p', type=int, default=REST_DEFAULT_SERVER_PORT,
        help=f'Port to bind to, default: {REST_DEFAULT_SERVER_PORT}')
    parser.add_argument(
        '--reload', '-r', action='store_true',
        help='Auto-reload server on filechanges (DEVELOPMENT)')
    args = parser.parse_args()

    uvicorn.run('xbox.rest.app:app', host=args.host, port=args.port, reload=args.reload)

if __name__ == '__main__':
    main()