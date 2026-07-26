/**
 * Day09 - HTTP 模块与原生 Web 服务器
 * 文件：router-server.js
 * 主题：手动路由分发 + query 参数解析 + 404 处理
 *
 * 演示：
 *   1. 用 new URL(req.url, base) 解析 pathname / query
 *   2. 对象映射式路由表：键 = "METHOD /path"
 *   3. query 参数读取（带默认值）
 *   4. 统一 JSON 响应封装 sendJSON
 *   5. 404 处理 + Content-Type 设置
 *
 * 运行：
 *   node Code/router-server.js
 *
 * 测试（另开终端）：
 *   curl http://localhost:3001/
 *   curl "http://localhost:3001/api/users?page=2&limit=20"
 *   curl http://localhost:3001/api/time
 *   curl -i http://localhost:3001/nope              # 看 404
 *   curl -i -X POST http://localhost:3001/api/users  # 路径存在但方法不允许，按 404 处理
 */

'use strict';

const http = require('http');

const PORT = 3001;

/**
 * 统一 JSON 响应封装
 * - 自动设 Content-Type
 * - 自动 stringify
 * - 默认状态码 200
 */
function sendJSON(res, data, statusCode = 200) {
  const body = JSON.stringify(data);
  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    // Content-Length 非必需，Node 会自动用 chunked；显式给可让客户端知道总长度
    'Content-Length': Buffer.byteLength(body),
  });
  res.end(body);
}

/**
 * 解析 req.url，返回 { method, pathname, query }
 * - query 是 URLSearchParams 实例，支持 .get / .has / .getAll
 * - 注意：req.url 不含 host，必须传一个 base
 */
function parseRequest(req) {
  const base = `http://${req.headers.host}`;
  const parsed = new URL(req.url, base);
  return {
    method: req.method,
    pathname: parsed.pathname,
    query: parsed.searchParams,
  };
}

// ---------------------------------------------------------------
// 路由表：键为 "METHOD /path"，值为处理函数
// 处理函数接收 { query, req } 返回 { status?, data }
// ---------------------------------------------------------------
const routes = {
  'GET /': () => ({
    data: { message: '首页', routes: ['/api/users', '/api/time'] },
  }),

  'GET /api/users': ({ query }) => {
    // query.get 在参数不存在时返回 null；用 ?? 提供默认值
    const page = Number(query.get('page')) || 1;
    const limit = Number(query.get('limit')) || 10;

    // 模拟分页返回
    const users = Array.from({ length: limit }, (_, i) => ({
      id: (page - 1) * limit + i + 1,
      name: `用户 ${(page - 1) * limit + i + 1}`,
    }));

    return {
      data: {
        page,
        limit,
        total: 100,
        items: users,
      },
    };
  },

  'GET /api/time': () => ({
    data: {
      iso: new Date().toISOString(),
      timestamp: Date.now(),
    },
  }),

  'GET /api/echo-headers': ({ req }) => ({
    // 演示读取请求头（注意 Node 把 header 名转成小写）
    data: {
      userAgent: req.headers['user-agent'],
      accept: req.headers['accept'],
      host: req.headers['host'],
      allHeaders: req.headers,
    },
  }),
};

// ---------------------------------------------------------------
// 创建服务器
// ---------------------------------------------------------------
const server = http.createServer((req, res) => {
  const { method, pathname, query } = parseRequest(req);
  console.log(`[${new Date().toISOString()}] ${method} ${pathname}${query.toString() ? '?' + query : ''}`);

  // 用 "METHOD /path" 作为路由键
  const key = `${method} ${pathname}`;
  const handler = routes[key];

  if (handler) {
    try {
      const { status, data } = handler({ query, req });
      sendJSON(res, data, status);
    } catch (err) {
      // 业务异常 → 500
      sendJSON(res, { error: 'internal error', message: err.message }, 500);
    }
    return;
  }

  // 路径存在但方法不支持的情况：本例简化处理统一返回 404
  // 严格按规范：可检查 pathname 是否在 routes 里出现过，若出现过则返回 405 Method Not Allowed
  const pathExists = Object.keys(routes).some((k) => k.endsWith(` ${pathname}`));
  if (pathExists) {
    sendJSON(res, {
      error: 'Method Not Allowed',
      method,
      path: pathname,
    }, 405);
  } else {
    sendJSON(res, { error: 'Not Found', path: pathname }, 404);
  }
});

server.listen(PORT, () => {
  console.log(`路由服务器已启动：http://localhost:${PORT}`);
  console.log('可用路由：');
  console.log('  GET /                       首页');
  console.log('  GET /api/users?page=&limit=  用户列表（分页）');
  console.log('  GET /api/time               当前时间');
  console.log('  GET /api/echo-headers        读取请求头');
  console.log('按 Ctrl+C 停止');
});
