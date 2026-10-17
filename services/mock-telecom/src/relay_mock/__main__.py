import os
from http.server import ThreadingHTTPServer
from .server import H

if __name__ == "__main__":
    ThreadingHTTPServer(
        (os.getenv("MOCK_HOST", "127.0.0.1"), int(os.getenv("MOCK_PORT", "8090"))), H
    ).serve_forever()
