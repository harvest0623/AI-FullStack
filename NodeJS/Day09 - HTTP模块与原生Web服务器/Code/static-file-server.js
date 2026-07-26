/**
 * Day09 - HTTP 模块与原生 Web 服务器
 * 文件：static-file-server.js
 * 主题：静态文件服务器 —— MIME 判断 / 404 / createReadStream 流式返回 / 防路径穿越
 *
 * 演示：
 *   1. path.extname 映射 Content-Type
 *   2. fs.createReadStream + pipe 流式返回（背压自动处理）
 *   3. 防路径穿越：用 path.normalize + startsWith 限制在根目录内
 *   4. 404 处理（文件不存在 / 越界访问）
 *   5. 自动找 index.html（根路径访问时）
 *
 * 运行：
 *   node Code/static-file-server.js
 *
 * 准备：
 *   在本文件同目录下建一个 public 文件夹，放些测试文件：
 *     public/index.html
 *     public/a.txt
 *     public/style.css
 *   （脚本启动时会自动创建一个示例 public/index.html 便于测试）
 *
 * 测试（另开终端）：
 *   curl http://localhost:3004/
 *   curl http://localhost:3004/index.html
 *   curl http://localhost:3004/a.txt
 *   curl -i http://localhost:3004/not-exist.txt        # 404
 *   curl -i "http://localhost:3004/../package.json"   # 路径穿越被拦截
 *   curl -i "http://localhost:3004/%2e%2e/package.json"  # URL 编码穿越也被拦
 */

'use strict';

const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3004;
const ROOT = path.join(__dirname, 'public');

// ---------------------------------------------------------------
// MIME 映射表
// 生产环境建议用 mime-types 包，覆盖更全
// ---------------------------------------------------------------
const MIME_MAP = {
  '.html': 'text/html; charset=utf-8',
  '.htm':  'text/html; charset=utf-8',
  '.css':  'text/css; charset=utf-8',
  '.js':   'text/javascript; charset=utf-8',
  '.mjs':  'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.txt':  'text/plain; charset=utf-8',
  '.md':   'text/markdown; charset=utf-8',
  '.xml':  'application/xml; charset=utf-8',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif':  'image/gif',
  '.svg':  'image/svg+xml',
  '.ico':  'image/x-icon',
  '.webp': 'image/webp',
  '.pdf':  'application/pdf',
  '.zip':  'application/zip',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
};

function getMimeType(filePath) {
  return MIME_MAP[path.extname(filePath).toLowerCase()] || 'application/octet-stream';
}

// ---------------------------------------------------------------
// 工具：发送文本响应（用于错误信息）
// ---------------------------------------------------------------
function sendText(res, text, statusCode = 200, contentType = 'text/plain; charset=utf-8') {
  res.writeHead(statusCode, {
    'Content-Type': contentType,
    'Content-Length': Buffer.byteLength(text),
  });
  res.end(text);
}

// ---------------------------------------------------------------
// 安全路径解析：防止路径穿越
// 攻击向量：/../etc/passwd 或 URL 编码 /%2e%2e/etc/passwd
// 解法：先用 path.join + path.normalize 拼成绝对路径，再校验是否仍在 ROOT 下
// ---------------------------------------------------------------
function safeResolve(urlPathname) {
  // decodeURIComponent 处理 URL 编码的 %2e%2e 等
  // 注意：WHATWG URL 已经对 pathname 做了一次解码，这里再解码一次是兜底
  // 实际上 new URL 已经解码过，这里 path.join 时若出现 .. 会被 normalize 折叠
  const resolved = path.normalize(path.join(ROOT, urlPathname));

  // 关键校验：必须在 ROOT 目录下（含 ROOT 本身）
  if (resolved !== ROOT && !resolved.startsWith(ROOT + path.sep)) {
    return null; // 越界
  }
  return resolved;
}

// ---------------------------------------------------------------
// 处理静态文件请求
// ---------------------------------------------------------------
function serveStatic(req, res, pathname) {
  // 1. 安全路径解析
  let filePath = safeResolve(pathname);
  if (!filePath) {
    return sendText(res, '403 Forbidden: path traversal blocked\n', 403);
  }

  // 2. 根路径自动找 index.html
  if (pathname === '/' || pathname.endsWith('/')) {
    filePath = path.join(filePath, 'index.html');
  }

  // 3. 用 fs.stat 判断文件是否存在 + 是文件还是目录
  fs.stat(filePath, (err, stats) => {
    if (err || !stats.isFile()) {
      // 不存在 → 404
      sendText(res, `404 Not Found: ${pathname}\n`, 404);
      return;
    }

    const mimeType = getMimeType(filePath);

    // 4. 写响应头：包含 Content-Type 与 Content-Length
    //    小文件用 readFile 一次读完也行，但流式更通用，下面统一用流
    res.writeHead(200, {
      'Content-Type': mimeType,
      'Content-Length': stats.size,
      // 简单缓存策略：静态资源 1 小时（生产建议用 hash 文件名做长期缓存）
      'Cache-Control': 'public, max-age=3600',
    });

    // 5. 用 createReadStream 把文件分块读出，pipe 到 res
    //    - pipe 内部处理背压（backpressure）：上游写太快时暂停读取，下游消化后再恢复
    //    - 因此即使文件 10GB，内存占用也稳定在很小
    //    - 流的错误事件必须监听，否则文件中途出错会让请求挂住
    const stream = fs.createReadStream(filePath);

    stream.on('error', (streamErr) => {
      // 流读取出错（如文件被中途删除）
      // 注意：响应头已经发出去，无法再改状态码，只能 end 掉
      console.error('文件流错误：', streamErr.message);
      if (!res.writableEnded) {
        res.end();
      }
    });

    // res 也是 Writable 流，pipe 完成后会自动调用 res.end()
    stream.pipe(res);
  });
}

// ---------------------------------------------------------------
// 创建服务器
// ---------------------------------------------------------------
const server = http.createServer((req, res) => {
  const parsed = new URL(req.url, `http://${req.headers.host}`);
  console.log(`[${new Date().toISOString()}] ${req.method} ${parsed.pathname}`);

  // 只处理 GET / HEAD；其他方法不支持
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    return sendText(res, '405 Method Not Allowed\n', 405, 'text/plain; charset=utf-8');
  }

  serveStatic(req, res, parsed.pathname);
});

// ---------------------------------------------------------------
// 启动前自动创建示例 public 目录与 index.html，方便直接测试
// ---------------------------------------------------------------
function ensureDemoFiles() {
  if (!fs.existsSync(ROOT)) fs.mkdirSync(ROOT, { recursive: true });

  const demoIndex = path.join(ROOT, 'index.html');
  if (!fs.existsSync(demoIndex)) {
    fs.writeFileSync(demoIndex, [
      '<!DOCTYPE html>',
      '<html lang="zh-CN">',
      '<head><meta charset="utf-8"><title>Day09 静态服务器示例</title></head>',
      '<body>',
      '  <h1>Hello from Day09 static-file-server</h1>',
      '  <p>这是脚本自动生成的示例页面。</p>',
      '  <p>试试访问：</p>',
      '  <ul>',
      '    <li><a href="/index.html">/index.html</a></li>',
      '    <li><a href="/a.txt">/a.txt</a></li>',
      '    <li><a href="/not-exist.txt">/not-exist.txt</a> (404)</li>',
      '  </ul>',
      '</body>',
      '</html>',
    ].join('\n'));
  }

  const demoTxt = path.join(ROOT, 'a.txt');
  if (!fs.existsSync(demoTxt)) {
    fs.writeFileSync(demoTxt, 'Day09 静态文件服务器示例文本。\n');
  }
}

ensureDemoFiles();

server.listen(PORT, () => {
  console.log(`静态文件服务器已启动：http://localhost:${PORT}`);
  console.log(`根目录：${ROOT}`);
  console.log('测试：');
  console.log('  curl http://localhost:3004/');
  console.log('  curl http://localhost:3004/index.html');
  console.log('  curl http://localhost:3004/a.txt');
  console.log('  curl -i http://localhost:3004/not-exist.txt          # 404');
  console.log('  curl -i "http://localhost:3004/../package.json"      # 路径穿越被拦');
  console.log('按 Ctrl+C 停止');
});
