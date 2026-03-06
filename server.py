import os
from wsgiref.simple_server import make_server


def app(environ, start_response):
    body = b"iGaruda Terminal backend is running."
    status = "200 OK"
    headers = [
        ("Content-Type", "text/plain; charset=utf-8"),
        ("Content-Length", str(len(body))),
    ]
    start_response(status, headers)
    return [body]


def main():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    with make_server(host, port, app) as server:
        print(f"Server listening on http://{host}:{port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
