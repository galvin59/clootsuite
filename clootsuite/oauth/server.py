"""Ephemeral HTTP server for OAuth callbacks."""

import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional
from urllib.parse import parse_qs, urlparse


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callbacks."""

    auth_code: Optional[str] = None
    event: Optional[asyncio.Event] = None

    def do_GET(self) -> None:
        """Handle GET request from OAuth provider.

        Expects: /callback?code=XXXX
        """
        parsed_url = urlparse(self.path)

        if parsed_url.path == "/callback":
            query_params = parse_qs(parsed_url.query)
            code = query_params.get("code", [None])[0]

            if code:
                OAuthCallbackHandler.auth_code = code

                # Send success response
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<html><body><h1>Authorization successful!</h1>"
                    b"<p>You can close this window.</p></body></html>"
                )

                # Signal that code was received
                if OAuthCallbackHandler.event:
                    OAuthCallbackHandler.event.set()
            else:
                # Error case
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<html><body><h1>Authorization failed!</h1>"
                    b"<p>No authorization code received.</p></body></html>"
                )
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        """Suppress HTTP server logging."""
        pass


class OAuthCallbackServer:
    """Ephemeral HTTP server for OAuth callbacks."""

    def __init__(self, port: int = 8080) -> None:
        """Initialize OAuth callback server.

        Args:
            port: Port to listen on.
        """
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.event = asyncio.Event()

    async def start(self) -> None:
        """Start the HTTP server.

        Runs indefinitely until shutdown() is called.
        """
        # Create server
        self.server = HTTPServer(("localhost", self.port), OAuthCallbackHandler)
        OAuthCallbackHandler.event = self.event

        # Run server in executor
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.server.serve_forever)

    async def wait_for_code(self) -> str:
        """Wait for OAuth code from callback.

        Returns:
            Authorization code.

        Raises:
            RuntimeError: If no code received.
        """
        await self.event.wait()

        code = OAuthCallbackHandler.auth_code
        if not code:
            raise RuntimeError("No authorization code received")

        return code

    async def shutdown(self) -> None:
        """Shutdown the HTTP server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
