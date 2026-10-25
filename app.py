"""Tiny web demo (stdlib only). Run: python app.py  ->  http://localhost:8000"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from sahulat.agent import ask

PAGE = """<!doctype html><meta charset=utf-8><title>Sahulat</title>
<body style="font-family:sans-serif;max-width:640px;margin:2rem auto;padding:0 1rem">
<h1>Sahulat</h1><p>Paste a bill or notice, ask in Urdu or English.</p>
<textarea id=q rows=6 style="width:100%"></textarea><br>
<button onclick="go()">Explain</button><pre id=a style="white-space:pre-wrap"></pre>
<script>async function go(){a.textContent='...';const r=await fetch('/ask',{method:'POST',
body:JSON.stringify({q:q.value})});a.textContent=(await r.json()).answer}</script>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._send(200, PAGE.encode(), "text/html; charset=utf-8")

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        answer = ask(str(body.get("q", ""))[:4000])
        self._send(200, json.dumps({"answer": answer}, ensure_ascii=False).encode(), "application/json")

    def _send(self, code, data, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
