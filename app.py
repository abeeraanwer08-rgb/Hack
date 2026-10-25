"""Sahulat web demo (Python stdlib only, no build step).

Run:  python app.py   ->  http://localhost:8000
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from sahulat.agent import ask
from sahulat.demo_data import EXAMPLES

HOST, PORT = "127.0.0.1", 8000

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sahulat — AI notice &amp; bill explainer</title>
<style>
  :root {
    --bg: #f4f6fb; --surface: #ffffff; --text: #17191f; --muted: #5b6270;
    --border: #e3e7ef; --accent: #0e7c61; --accent-ink: #ffffff;
    --bubble-user: #0e7c61; --bubble-assistant: #eef1f6; --radius: 14px;
    --shadow: 0 1px 2px rgba(20,20,30,.04), 0 8px 24px rgba(20,20,30,.06);
  }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#0e1117; --surface:#161b22; --text:#e8ebf1; --muted:#9aa3b2;
      --border:#262c38; --accent:#2fbf8f; --accent-ink:#06211a;
      --bubble-user:#2fbf8f; --bubble-assistant:#1f2530;
      --shadow: 0 1px 2px rgba(0,0,0,.3), 0 8px 24px rgba(0,0,0,.4); }
  }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--text);
    font-family: -apple-system, "Segoe UI", Roboto, "Noto Sans", "Noto Nastaliq Urdu", sans-serif; }
  .wrap { max-width: 720px; margin: 0 auto; padding: 1.25rem 1rem 3rem; }
  header { display:flex; align-items:center; gap:.65rem; padding: .5rem 0 1.1rem; }
  .logo { width:38px; height:38px; border-radius:10px; background:linear-gradient(135deg,var(--accent),#1aa37a);
    display:flex; align-items:center; justify-content:center; font-size:1.2rem; flex:none; }
  h1 { font-size:1.3rem; margin:0; }
  .tagline { color:var(--muted); font-size:.85rem; margin:0; }
  .card { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius);
    box-shadow:var(--shadow); padding:1rem; }
  .examples { display:flex; flex-wrap:wrap; gap:.5rem; margin-bottom: .9rem; }
  .chip { border:1px solid var(--border); background:var(--bg); color:var(--text); border-radius:999px;
    padding:.4rem .8rem; font-size:.82rem; cursor:pointer; transition:.15s; }
  .chip:hover { border-color: var(--accent); color: var(--accent); }
  textarea { width:100%; min-height:110px; resize:vertical; border:1px solid var(--border);
    border-radius:10px; padding:.7rem .8rem; font-size:.95rem; background:var(--bg); color:var(--text);
    font-family:inherit; }
  textarea:focus { outline:2px solid var(--accent); outline-offset:1px; }
  .row { display:flex; align-items:center; gap:.5rem; margin-top:.7rem; flex-wrap:wrap; }
  button.primary { background:var(--accent); color:var(--accent-ink); border:none; border-radius:10px;
    padding:.6rem 1.1rem; font-weight:600; font-size:.9rem; cursor:pointer; }
  button.primary:disabled { opacity:.6; cursor:default; }
  button.icon { background:var(--bg); border:1px solid var(--border); color:var(--text); border-radius:10px;
    width:38px; height:38px; cursor:pointer; font-size:1rem; }
  button.icon[aria-pressed="true"] { border-color:var(--accent); color:var(--accent); }
  .spacer { flex:1; }
  select { border:1px solid var(--border); background:var(--bg); color:var(--text); border-radius:8px;
    padding:.45rem .6rem; font-size:.85rem; }
  .chat { margin-top:1.1rem; display:flex; flex-direction:column; gap:.6rem; }
  .msg { max-width:88%; padding:.65rem .85rem; border-radius:12px; line-height:1.45; font-size:.93rem;
    white-space:pre-wrap; }
  .msg.user { align-self:flex-end; background:var(--bubble-user); color:var(--accent-ink); border-bottom-right-radius:3px; }
  .msg.assistant { align-self:flex-start; background:var(--bubble-assistant); color:var(--text); border-bottom-left-radius:3px; }
  .msg[dir="rtl"] { text-align:right; font-family:"Noto Nastaliq Urdu", "Jameel Noori Nastaleeq", serif; font-size:1.02rem; }
  .meta { color:var(--muted); font-size:.72rem; margin-top:.25rem; }
  .dots::after { content:"●"; animation: blink 1s infinite; }
  @keyframes blink { 50% { opacity:.2; } }
  footer { color:var(--muted); font-size:.75rem; text-align:center; margin-top:1.4rem; }
  footer a { color: var(--accent); }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="logo">📄</div>
    <div>
      <h1>Sahulat</h1>
      <p class="tagline">Paste a bill, court notice, tax notice or flood alert — ask in Urdu or English.</p>
    </div>
  </header>

  <div class="card">
    <div class="examples" id="examples"></div>
    <textarea id="q" placeholder="Paste or type the notice here… / یہاں نوٹس پیسٹ کریں"></textarea>
    <div class="row">
      <button class="icon" id="mic" title="Voice input">🎤</button>
      <button class="icon" id="speak" title="Read last reply aloud" aria-pressed="false">🔊</button>
      <select id="lang" title="Reply language">
        <option value="auto">Auto language</option>
        <option value="en">English</option>
        <option value="ur">اردو</option>
      </select>
      <span class="spacer"></span>
      <button class="primary" id="send">Explain</button>
    </div>
  </div>

  <div class="chat" id="chat"></div>
  <footer>Powered by Qwen · Alibaba Cloud Model Studio — not legal advice, verify with the issuing office.</footer>
</div>
<script>
const chat = document.getElementById('chat');
const qEl = document.getElementById('q');
const sendBtn = document.getElementById('send');
const micBtn = document.getElementById('mic');
const speakBtn = document.getElementById('speak');
const langSel = document.getElementById('lang');
let lastReply = "";

function isRtl(s) { return /[\\u0600-\\u06FF]/.test(s); }

function addMsg(role, text) {
  const d = document.createElement('div');
  d.className = 'msg ' + role;
  if (isRtl(text)) d.setAttribute('dir', 'rtl');
  d.textContent = text;
  chat.appendChild(d);
  chat.scrollTop = chat.scrollHeight;
  return d;
}

async function send() {
  const text = qEl.value.trim();
  if (!text) return;
  addMsg('user', text);
  qEl.value = '';
  sendBtn.disabled = true;
  const pending = addMsg('assistant', '');
  pending.innerHTML = '<span class="dots">thinking</span>';
  try {
    const r = await fetch('/ask', { method: 'POST', body: JSON.stringify({ q: text, lang: langSel.value }) });
    const data = await r.json();
    lastReply = data.answer;
    pending.innerHTML = '';
    pending.textContent = data.answer;
    if (isRtl(data.answer)) pending.setAttribute('dir', 'rtl');
  } catch (e) {
    pending.textContent = 'Network error. Is the server running?';
  } finally {
    sendBtn.disabled = false;
  }
}
sendBtn.onclick = send;
qEl.addEventListener('keydown', (e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) send(); });

// Example chips, loaded from the server so Python stays the single source of truth.
fetch('/examples').then(r => r.json()).then(list => {
  const box = document.getElementById('examples');
  list.forEach(ex => {
    const b = document.createElement('button');
    b.className = 'chip';
    b.textContent = ex.label;
    b.onclick = () => { qEl.value = ex.text; qEl.focus(); };
    box.appendChild(b);
  });
});

// Voice input (Web Speech API) — feature-detected, hidden if the browser lacks it.
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
if (!SR) { micBtn.style.display = 'none'; }
else {
  const rec = new SR();
  rec.continuous = false;
  rec.onresult = (e) => { qEl.value += (qEl.value ? ' ' : '') + e.results[0][0].transcript; };
  rec.onstart = () => micBtn.setAttribute('aria-pressed', 'true');
  rec.onend = () => micBtn.setAttribute('aria-pressed', 'false');
  micBtn.onclick = () => rec.start();
}

// Read the last reply aloud (speechSynthesis) — also feature-detected.
if (!window.speechSynthesis) { speakBtn.style.display = 'none'; }
else {
  speakBtn.onclick = () => {
    if (!lastReply) return;
    const u = new SpeechSynthesisUtterance(lastReply);
    u.lang = isRtl(lastReply) ? 'ur-PK' : 'en-US';
    speechSynthesis.cancel();
    speechSynthesis.speak(u);
  };
}
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # keep the demo console quiet

    def do_GET(self):
        if self.path == "/examples":
            self._json(200, EXAMPLES)
        else:
            self._send(200, PAGE.encode(), "text/html; charset=utf-8")

    def do_POST(self):
        if self.path != "/ask":
            self._send(404, b"not found", "text/plain")
            return
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        question = str(body.get("q", ""))[:4000]
        answer = ask(question) if question else "Please type or paste something first."
        self._json(200, {"answer": answer})

    def _json(self, code, obj):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def _send(self, code, data, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    print(f"Sahulat running at http://{HOST}:{PORT}")
    HTTPServer((HOST, PORT), Handler).serve_forever()
