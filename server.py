#!/usr/bin/env python3
"""局域网字体服务器：提供 iOS 描述文件与安装说明页。

- .mobileconfig 用 application/x-apple-aspen-config 内容类型（Safari 识别）
- 不做 gzip 压缩：Safari 下载描述文件交给 iOS 安装器时可能不解压，
  压缩传输会导致安装器拿到二进制乱码而报「包含无效字体」
"""
import http.server
import os
import socketserver

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("FONT_SERVER_PORT", "8000"))


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".mobileconfig": "application/x-apple-aspen-config",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

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
