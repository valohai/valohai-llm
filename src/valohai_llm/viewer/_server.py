"""Lightweight HTTP server for the results viewer."""

from __future__ import annotations

import http.server
import logging
import socket
import webbrowser
from typing import Any

from valohai_llm.viewer._app_html import generate_html

logger = logging.getLogger(__name__)


class _ViewerHandler(http.server.BaseHTTPRequestHandler):
    _html: bytes = b""

    def do_GET(self) -> None:
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(self._html)))
            self.end_headers()
            self.wfile.write(self._html)
        else:
            self.send_error(404)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        logger.debug(format, *args)


def serve(
    results: list[dict[str, Any]],
    *,
    port: int = 0,
    open_browser: bool = True,
    host: str = "127.0.0.1",
) -> None:
    """Serve the results viewer on a local HTTP server.

    Args:
        results: List of result dicts with ``metrics``, ``labels``, etc.
        port: TCP port to bind to. ``0`` picks a free port automatically.
        open_browser: Open the viewer in the default web browser.
        host: Host to bind to.
    """
    html = generate_html(results)
    _ViewerHandler._html = html.encode("utf-8")

    server = http.server.HTTPServer((host, port), _ViewerHandler)
    server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    actual_port = server.server_address[1]
    url = f"http://{host}:{actual_port}/"

    print(f"Results viewer running at {url}")  # noqa: T201
    print("Press Ctrl+C to stop.")  # noqa: T201

    if open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
