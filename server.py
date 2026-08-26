#!/usr/bin/env python3
"""局域网字体服务器：提供 iOS 描述文件与安装说明页。

- 静态页 + 已生成描述文件（profiles/）
- GET /fonts.json：可用字体列表（供页面勾选）
- POST /api/profile：按勾选的字体动态生成描述文件（二进制 plist）
- .mobileconfig 用 application/x-apple-aspen-config 内容类型（Safari 识别）
- 不做 gzip 压缩：Safari 下载描述文件交给 iOS 安装器时可能不解压，
  压缩传输会导致安装器拿到二进制乱码而报「包含无效字体」
"""
import http.server
import json
import os
import socketserver
import urllib.parse

from generate_profile import discover_fonts, display_name, make_profile

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("FONT_SERVER_PORT", "8765"))


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".mobileconfig": "application/x-apple-aspen-config",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/fonts.json":
            self._send_json(self._font_list())
            return
        if parsed.path == "/profiles.json":
            self._send_json(self._profile_list())
            return
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/api/profile":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        try:
            req = json.loads(body.decode("utf-8", errors="replace") or "{}")
        except json.JSONDecodeError:
            self.send_error(400, "bad json")
            return
        selected = req.get("fonts") or []
        by_name = {p.name: p for p in discover_fonts()}
        missing = [n for n in selected if n not in by_name]
        if missing:
            self.send_error(400, f"未知字体: {missing}")
            return
        fonts = [by_name[n] for n in selected if n in by_name]
        if not fonts:
            self.send_error(400, "未选择字体")
            return
        desc = req.get("name") or f"{len(fonts)} 个字体"
        data = make_profile("custom", fonts, desc)
        self.send_response(200)
        self.send_header("Content-Type", "application/x-apple-aspen-config")
        self.send_header("Content-Disposition", 'attachment; filename="fonts.mobileconfig"')
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _font_list(self):
        return [
            {"name": p.name, "display": display_name(p), "size": p.stat().st_size}
            for p in discover_fonts()
        ]

    def _profile_list(self):
        """列出预生成的描述文件（profiles/ 下的 .mobileconfig）。"""
        profiles_dir = os.path.join(ROOT, "profiles")
        out = []
        if os.path.isdir(profiles_dir):
            for name in sorted(os.listdir(profiles_dir)):
                if not name.endswith(".mobileconfig"):
                    continue
                path = os.path.join(profiles_dir, name)
                out.append({"name": name, "size": os.path.getsize(path)})
        return out

    def _send_json(self, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        print(f"[{self.address_string()}] {fmt % args}", flush=True)


class ThreadingServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def local_ips() -> list:
    import socket
    ips = set()
    try:
        hostname = socket.gethostname()
        ips.update(socket.gethostbyname_ex(hostname)[2])
    except OSError:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    return sorted(ips)


if __name__ == "__main__":
    with ThreadingServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"字体服务器已启动（局域网可访问）: http://0.0.0.0:{PORT}")
        for ip in local_ips():
            print(f"  ->  http://{ip}:{PORT}/")
        print("在 iPhone Safari 中打开上面的地址，点按「下载并安装」。", flush=True)
        httpd.serve_forever()
