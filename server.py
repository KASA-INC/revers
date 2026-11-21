#!/usr/bin/env python3
"""Lokal server for Revers: serverer webappen og lagrer videoer i mappen videoer/."""
import os
import re
import json
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(ROOT, "videoer")
PORT = int(os.environ.get("PORT", 8765))
MAX_BYTES = 500 * 1024 * 1024


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        # Tillat lagring også når siden er åpnet som fil (file://) eller fra en annen adresse
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "X-Filename, Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_POST(self):
        if self.path != "/save":
            return self.send_error(404)
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0 or length > MAX_BYTES:
            return self.send_error(400, "Ugyldig størrelse")
        name = self.headers.get("X-Filename", "revers.webm")
        name = re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(name)) or "revers.webm"
        if not name.lower().endswith((".mp4", ".webm")):
            name += ".webm"
        os.makedirs(SAVE_DIR, exist_ok=True)
        base, ext = os.path.splitext(name)
        path, n = os.path.join(SAVE_DIR, name), 1
        while os.path.exists(path):
            path = os.path.join(SAVE_DIR, f"{base}-{n}{ext}")
            n += 1
        with open(path, "wb") as f:
            remaining = length
            while remaining > 0:
                chunk = self.rfile.read(min(1 << 20, remaining))
                if not chunk:
                    break
                f.write(chunk)
                remaining -= len(chunk)
        body = json.dumps({"saved": os.path.relpath(path, ROOT)}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    print(f"Revers kjører på http://localhost:{PORT} – videoer lagres i {SAVE_DIR}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
