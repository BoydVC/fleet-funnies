#!/usr/bin/env python3
"""Fleet Funnies server: 127.0.0.1:4142. Serves web/ plus /data, /dist, /strips (read-only)."""
import os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get('PORT', '4142'))

class H(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        p = path.split('?', 1)[0].split('#', 1)[0]
        for pre in ('/data/', '/dist/', '/strips/'):
            if p.startswith(pre):
                full = os.path.normpath(os.path.join(ROOT, p.lstrip('/')))
                return full if full.startswith(os.path.join(ROOT, pre.strip('/'))) else os.path.join(ROOT, 'web', '404')
        if p == '/api/health':
            return os.path.join(ROOT, 'web', 'health.json')
        self.directory = os.path.join(ROOT, 'web')
        return super().translate_path(path)
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()
    def log_message(self, *a):
        pass

if __name__ == '__main__':
    os.chdir(os.path.join(ROOT, 'web'))
    print(f'Fleet Funnies on http://127.0.0.1:{PORT}/', flush=True)
    ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()
