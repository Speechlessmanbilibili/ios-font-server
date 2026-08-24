# iOS 字体安装服务器（Hanlink Sans + CJK Punct Bridge）

通过 iOS 配置描述文件（`.mobileconfig`）在局域网内给 iPhone/iPad 安装字体。
一个描述文件可以内嵌 **36 个静态字体**：Hanlink Sans 9 正体 + 9 斜体，
CJK Punct Bridge 9 正体 + 9 斜体标点字体，实测一次全装成功。

## 快速开始

```bash
pip install fonttools

# 1. 生成描述文件（依赖本机已有的字体静态目录）
python generate_profile.py

# 2. 启动局域网服务器（默认 0.0.0.0:8000）
python server.py
```

手机 Safari 打开 `http://<电脑局域网IP>:8000/`，点页面顶部的全量包按钮，
下载后在「设置 → 已下载描述文件 → 安装」，再到「设置 → 通用 → 字体」启用。

> 描述文件默认按字重「正体 + 斜体」两两配对，另附一个 36 字体全量包。
> 生成物在 `profiles/`（已 gitignore），按需本地生成，不提交仓库。

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `generate_profile.py` | 从字体静态目录生成 `.mobileconfig`（二进制 plist） |
| `server.py` | 局域网 HTTP 服务器，`.mobileconfig` 以 `application/x-apple-aspen-config` 提供 |
| `index.html` | 安装页：全量下载 + 配对下载 + 安装步骤 |
| `fonts/` 引用 | 脚本读取 `../hanlink-sans/fonts/static` 与 `../CJK-Punct-Bridge/fonts/static`（可改） |

字体来源：Hanlink Sans（[Speechlessmanbilibili/Hanlink-Sans](https://github.com/Speechlessmanbilibili/Hanlink-Sans)）与
CJK Punct Bridge（[Speechlessmanbilibili/CJK-Punct-Bridge](https://github.com/Speechlessmanbilibili/CJK-Punct-Bridge)）。

## 排障经验：iOS 报「包含无效字体」

以下是本项目的完整排障记录。iOS 的 `com.apple.font` payload 只支持 **base64 内嵌
字体**（无远程 URL 键），报「包含无效字体」通常不是字体本身的问题，而是描述文件
的生成方式。逐条排查，按可能性从高到低：

### 1. 双重 base64 编码（本项目真凶）

`Font` 键**必须传原始字体字节**，由 plistlib 序列化时自行 base64 编码：

```python
"Font": path.read_bytes(),          # ✅ 正确
"Font": base64.b64encode(path.read_bytes()),   # ❌ 双重编码
```

如果先 `b64encode` 一次再交给 plistlib，XML 输出时会被**再编码一次**。
iOS 解码一次后拿到的是 base64 文本而非字体数据，CoreText 加载失败 → 报
「包含无效字体」。二进制 plist 同样中招（存进去的是 base64 文本字节）。
排查时用树级 diff 对比「可用 profile」与「自己的 profile」的 `Font` 值，
立刻就能看出存的是 `\x00\x01\x00\x00`（TTF 魔数）还是 `AAEAAAAR...`（base64 文本）。

### 2. `Name` 键缺失

`com.apple.font` payload 有一个**必需键 `Name`**（值为字体文件名，如
`HanlinkSans-Regular.ttf`），Apple 文档示例和 keyman 实测 profile 中都有。
缺失时 iOS 直接判定「包含无效字体」。注意 `PayloadDisplayName` 不能替代它。

### 3. 服务器不要对 `.mobileconfig` 做 gzip 压缩

Safari 下载描述文件交给系统安装器时可能**不解压**，如果服务器返回
`Content-Encoding: gzip`，安装器拿到的是 gzip 二进制乱码 → 解析失败。
局域网场景直接传原始文件即可（大文件慢一点但正确）。

### 4. Content-Type 只能有一个，且必须正确

必须 `application/x-apple-aspen-config`。注意不要用 `end_headers()` 追加头——
`SimpleHTTPRequestHandler` 已经发过默认的 `application/octet-stream`，追加会
产生**两个 Content-Type 头**，iOS 可能认错。正确做法是覆盖 `extensions_map`：

```python
class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".mobileconfig": "application/x-apple-aspen-config",
    }
```

### 5. 关于「15–20MB 描述文件上限」的传言

社区流传 iOS 无法安装大于 15–20MB 的描述文件（如思源宋体 16MB 失败），
但本项目的 189.7MB 全量包（36 个字体）在修复上述问题后**实测一次装成功**。
此前大文件失败很可能也是编码/格式问题，而非大小限制本身。
如果仍担心，可以按字重两两配对生成小包（本项目 `profiles/` 里两种都有）。

### 6. 调试方法论：黄金标准对照实验

找不到头绪时，用「确定可用」的 profile 做黄金标准逐步对照（本项目使用了
[keyman 的字体 profile](https://github.com/keymanapp/r.keymanweb.com)）：

1. **模板替换字体**：把可用 profile 的 `<data>` 替换成自己的字体 ——
   隔离「字体因素」：能装则字体没问题；
2. **重新序列化**：用 plistlib 重新 dump 可用 profile 的全部原值 ——
   隔离「序列化器因素」：能装则 plistlib 输出格式没问题；
3. **单变量修改**：在可用基底上每次只改一个值（identifier、UUID 大小写、
   中文文案等）——逐个排除「值因素」；
4. **树级 diff**：递归对比两棵 plist 的所有键值，最终定位到 `Font` 值
   的编码差异（双重 base64 就是这么抓出来的）。

## 许可证

- 字体：Hanlink Sans 与 CJK Punct Bridge 均为 [SIL Open Font License 1.1](LICENSE)
- 本项目工具代码同样以 OFL 1.1 发布
- 排障参考了 keyman（[r.keymanweb.com](https://github.com/keymanapp/r.keymanweb.com)）公开的字体描述文件结构
