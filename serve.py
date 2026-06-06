# -*- coding: utf-8 -*-
"""Sirve el dashboard en http://localhost:3140"""
import http.server, os
from http.server import ThreadingHTTPServer
os.chdir(os.path.dirname(os.path.abspath(__file__)))
PORT = 3140
class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()
    def log_message(self, *a): pass
httpd = ThreadingHTTPServer(("", PORT), H)
httpd.daemon_threads = True
print(f"Dashboard SUCIVE Motos -> http://localhost:{PORT}/dashboard.html")
httpd.serve_forever()
