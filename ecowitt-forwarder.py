#!/usr/bin/env python3
# ecowitt-forwarder.py
#
# Lightweight Ecowitt -> WeeWX Interceptor relay (no Flask, no Docker).
# Listens on /data/report and forwards the same params to Interceptor.
#
# HP2551 "Customized" upload:
#   Server: http://<PI_IP>
#   Port: 8000   (match LISTEN_PORT)
#   Path: /data/report
#
# WeeWX Interceptor (weewx.conf):
#   [Station]
#   station_type = Interceptor
#   [Interceptor]
#   mode = ecowitt
#   port = 46000     (match FORWARD_URL below)

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
from urllib.request import urlopen, Request
import sys

# ------- CONFIG -------
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 8080

# Interceptor usually listens on 46000; include the path!
FORWARD_URL = "http://127.0.0.1:46000/data/report"
FORWARD_TIMEOUT = 5.0
# ----------------------

def _flatten(qs_dict):
    """parse_qs returns lists; flatten to single values when appropriate."""
    flat = {}
    for k, v in qs_dict.items():
        if isinstance(v, list) and len(v) == 1:
            flat[k] = v[0]
        else:
            # if multiple values appear, join with comma (rare for Ecowitt)
            flat[k] = ",".join(v) if isinstance(v, list) else str(v)
    return flat

class EcowittRelay(BaseHTTPRequestHandler):
    def _handle(self):
        # Accept GET (query string) and POST (x-www-form-urlencoded)
        if self.command == "GET":
            parsed = urlparse(self.path)
            if parsed.path != "/data/report":
                # Ecowitt sometimes probes / or favicon — reply 200 so console doesn't complain
                self._write_ok("OK")
                return
            data = _flatten(parse_qs(parsed.query))

        elif self.command == "POST":
            # Ecowitt uses application/x-www-form-urlencoded
            length = int(self.headers.get("Content-Length", "0") or "0")
            body = self.rfile.read(length).decode("utf-8", errors="replace") if length > 0 else ""
            data = _flatten(parse_qs(body))
        else:
            self._write_ok("OK")
            return

        if not data:
            self.log_message("Received empty packet")
            self._write_ok("OK: empty")
            return

        self.log_message("Rx keys: %s", ",".join(sorted(data.keys())))

        # Forward to Interceptor as GET with same params
        try:
            qs = urlencode(data)
            url = f"{FORWARD_URL}?{qs}"
            req = Request(url, method="GET")
            with urlopen(req, timeout=FORWARD_TIMEOUT) as resp:
                self.log_message("Forward -> Interceptor %s", resp.status)
        except Exception as e:
            self.log_message("Forward error: %s", e)

        # Always return 200 to the console so uploads continue
        self._write_ok("OK")

    def do_GET(self):
        self._handle()

    def do_POST(self):
        self._handle()

    def log_message(self, fmt, *args):
        sys.stdout.write("[relay] " + (fmt % args) + "\n")
        sys.stdout.flush()

    def _write_ok(self, msg="OK"):
        body = msg.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

def main():
    srv = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), EcowittRelay)
    print(f"Ecowitt relay listening on http://{LISTEN_HOST}:{LISTEN_PORT}/data/report")
    print(f"Forwarding to Interceptor at: {FORWARD_URL}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        srv.shutdown()

if __name__ == "__main__":
    main()

