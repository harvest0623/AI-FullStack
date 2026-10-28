# -*- coding: utf-8 -*-
"""
Day10 - 03 服务化：把客服封装成 HTTP 接口

用 Python 标准库 http.server 起一个最小服务：
- POST /chat  body: {"session_id": "...", "message": "..."}  -> {"reply": "..."}
- GET  /health -> {"status":"ok"}

运行后访问 http://127.0.0.1:8000 即可测试。Ctrl+C 停止。
离线可运行（内部走 SimOllama）。
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from ollama_util import chat_wrapper

# 每个 session 一个历史（复用 Day06 的会话隔离思路）
_sessions: dict[str, list[dict]] = {}
_lock = threading.Lock()


def _get_history(sid: str) -> list[dict]:
    with _lock:
        if sid not in _sessions:
            _sessions[sid] = [
                {"role": "system", "content": "你是本地客服小O。"}]
        return _sessions[sid]


def ask(sid: str, message: str) -> str:
    history = _get_history(sid)
    history.append({"role": "user", "content": message})
    reply = chat_wrapper(history)
    history.append({"role": "assistant", "content": reply})
    return reply


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"status": "ok"})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/chat":
            self._send(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode()
        try:
            data = json.loads(raw)
            sid = data.get("session_id", "default")
            msg = data.get("message", "")
            reply = ask(sid, msg)
            self._send(200, {"reply": reply})
        except Exception as e:  # 健壮性：给调用方错误信息
            self._send(500, {"error": str(e)})

    def log_message(self, fmt, *args):
        print(f"[http] {self.command} {self.path}")


def main():
    port = 8000
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f">> 客服服务已启动: http://127.0.0.1:{port}")
    print("   POST /chat  {\"session_id\":\"u1\",\"message\":\"你好\"}")
    print("   GET  /health  健康检查")
    print("   Ctrl+C 停止\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止。")


if __name__ == "__main__":
    main()