/**
 * Day09 - HTTP 模块与原生 Web 服务器
 * 文件：json-api-server.js
 * 主题：JSON API 服务器 —— GET 返回数据 / POST 接收 JSON / CORS / OPTIONS 预检
 *
 * 演示：
 *   1. 统一 CORS 头处理（含 OPTIONS 预检）
 *   2. readBody(req) 工具：把请求体收集 + 大小限制 + 解析为 JSON/表单
 *   3. POST /api/echo：解析 JSON 请求体，校验字段，返回处理结果
 *   4. 错误状态码：400（参数错）/ 413（包太大）
 *   5. Content-Type 必须对上，否则不解析
 *
 * 运行：
 *   node Code/json-api-server.js
 *
 * 测试（另开终端）：
 *   # 1. 简单 GET
 *   curl http://localhost:3002/api/ping
 *
 *   # 2. CORS 预检 OPTIONS（前端跨域发 JSON 时浏览器先发这个）
 *   curl -X OPTIONS http://localhost:3002/api/echo \
 *     -H "Origin: http://localhost:5173" \
 *     -H "Access-Control-Request-Method: POST" \
 *     -H "Access-Control-Request-Headers: Content-Type" -i
 *
 *   # 3. POST JSON
 *   curl -X POST http://localhost:3002/api/echo \
 *     -H "Content-Type: application/json" \
 *     -d '{"message":"hi from curl"}'
 *
 *   # 4. 故意发坏 JSON（期望 400）
 *   curl -X POST http://localhost:3002/api/echo \
 *     -H "Content-Type: application/json" \
 *     -d 'not-a-json'
 *
 *   # 5. 字段缺失（期望 400）
 *   curl -X POST http://localhost:3002/api/echo \
 *     -H "Content-Type: application/json" \
 *     -d '{"foo":"bar"}'
 *
 *   # 6. 表单请求（演示 x-www-form-urlencoded 解析）
 *   curl -X POST http://localhost:3002/api/form \
 *     -H "Content-Type: application/x-www-form-urlencoded" \
 *     -d 'name=Alice&age=18'
 *
 *   # 7. 请求体过大（期望 413）
 *   curl -X POST http://localhost:3002/api/echo \
 *     -H "Content-Type: application/json" \
 *     -d "$(node -e "process.stdout.write(JSON.stringify({message:'x'.repeat(2*1024*1024)}))")"
 */

'use strict';

const http = require('http');

const PORT = 3002;
const MAX_BODY = 1024 * 1024; // 1MB 上限

// ---------------------------------------------------------------
// 工具函数：统一 JSON 响应
// ---------------------------------------------------------------
function sendJSON(res, data, statusCode = 200, extraHeaders = {}) {
  const body = JSON.stringify(data);
  const headers = {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(body),
    ...extraHeaders,
  };
  res.writeHead(statusCode, headers);
  res.end(body);
}

// ---------------------------------------------------------------
// CORS 中间件：设置跨域响应头
// - 返回 true 表示这是 OPTIONS 预检，已直接响应，业务逻辑应跳过
// - 返回 false 表示继续走业务路由
// ---------------------------------------------------------------
function applyCors(req, res) {
  // Allow-Origin：生产环境建议改成白名单，而不是 *
  // 这里为了演示方便用 *
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  // Allow-Headers 必须包含前端会用到的所有自定义头
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  // 预检结果缓存 1 天，减少 OPTIONS 请求
  res.setHeader('Access-Control-Max-Age', '86400');

  // 预检请求：直接 204 No Content 返回，不进业务逻辑
  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return true;
  }
  return false;
}

// ---------------------------------------------------------------
// 工具函数：读取请求体
// - req 是 Readable 流，分块到达，需用 data/end 事件收集
// - 用 Buffer.concat 而非字符串拼接，避免多字节字符拆分乱码
// - 累计大小超过上限时主动中断，避免被恶意大包打 OOM
// - 按 Content-Type 选择解析方式
// ---------------------------------------------------------------
function readBody(req, { maxBytes = MAX_BODY } = {}) {
  return new Promise((resolve, reject) => {
    const contentType = (req.headers['content-type'] || '').toLowerCase();
    const chunks = [];
    let size = 0;

    req.on('data', (chunk) => {
      size += chunk.length;
      if (size > maxBytes) {
        // 自定义错误码，业务层据此返回 413
        const err = new Error(`请求体超过 ${maxBytes} 字节上限`);
        err.code = 'BODY_TOO_LARGE';
        // 主动 destroy，停止读取
        req.destroy();
        reject(err);
        return;
      }
      chunks.push(chunk);
    });

    req.on('end', () => {
      const buf = Buffer.concat(chunks);
      const text = buf.toString('utf8');

      // 没有请求体（如 GET），返回 null
      if (!text) return resolve(null);

      // 按 Content-Type 分流解析
      if (contentType.includes('application/json')) {
        try {
          resolve({ type: 'json', data: JSON.parse(text) });
        } catch (e) {
          const err = new Error('JSON 格式错误');
          err.code = 'INVALID_JSON';
          reject(err);
        }
        return;
      }

      if (contentType.includes('application/x-www-form-urlencoded')) {
        // URLSearchParams 直接处理 a=1&b=2 形式
        const params = new URLSearchParams(text);
        const data = {};
        for (const [k, v] of params.entries()) data[k] = v;
        resolve({ type: 'form', data });
        return;
      }

      // 其他类型：当纯文本返回
      resolve({ type: 'text', data: text });
    });

    req.on('error', (err) => reject(err));
  });
}

// ---------------------------------------------------------------
// 路由处理：每个 handler 接收 { req, res, parsed, query, body? }
// ---------------------------------------------------------------
async function handleRoute({ req, res, pathname, query, body }) {
  // GET /api/ping：心跳
  if (pathname === '/api/ping' && req.method === 'GET') {
    return sendJSON(res, { ok: true, time: new Date().toISOString() });
  }

  // POST /api/echo：接收 JSON，校验后返回
  if (pathname === '/api/echo' && req.method === 'POST') {
    // body.type 必须是 json
    if (!body || body.type !== 'json') {
      return sendJSON(res, { error: 'Content-Type 必须是 application/json' }, 400);
    }
    const data = body.data;
    // 字段校验：必须有 message 字段且非空字符串
    if (typeof data.message !== 'string' || data.message.length === 0) {
      return sendJSON(res, { error: '字段 message 必填且为非空字符串' }, 400);
    }
    // 模拟业务处理：原样回显 + 时间戳
    return sendJSON(res, {
      received: data.message,
      length: data.message.length,
      processedAt: new Date().toISOString(),
    });
  }

  // POST /api/form：演示表单解析
  if (pathname === '/api/form' && req.method === 'POST') {
    if (!body || body.type !== 'form') {
      return sendJSON(res, { error: 'Content-Type 必须是 application/x-www-form-urlencoded' }, 400);
    }
    return sendJSON(res, { received: body.data });
  }

  // POST /api/users：模拟创建（演示 201 Created 状态码）
  if (pathname === '/api/users' && req.method === 'POST') {
    if (!body || body.type !== 'json') {
      return sendJSON(res, { error: 'Content-Type 必须是 application/json' }, 400);
    }
    const { name, email } = body.data || {};
    if (!name || !email) {
      return sendJSON(res, { error: 'name 和 email 必填' }, 422);
    }
    return sendJSON(res, {
      id: Math.floor(Math.random() * 1000) + 1,
      name,
      email,
      createdAt: new Date().toISOString(),
    }, 201);
  }

  // 未匹配
  return sendJSON(res, { error: 'Not Found', path: pathname }, 404);
}

// ---------------------------------------------------------------
// 创建服务器
// ---------------------------------------------------------------
const server = http.createServer(async (req, res) => {
  const parsed = new URL(req.url, `http://${req.headers.host}`);
  console.log(`[${new Date().toISOString()}] ${req.method} ${parsed.pathname}`);

  // 1. CORS 中间件：处理 OPTIONS 预检
  if (applyCors(req, res)) return;

  // 2. 业务路由
  try {
    // GET / DELETE 通常无请求体；POST / PUT / PATCH 才需要读取
    const hasBody = ['POST', 'PUT', 'PATCH'].includes(req.method);
    const body = hasBody ? await readBody(req) : null;

    await handleRoute({
      req, res,
      pathname: parsed.pathname,
      query: parsed.searchParams,
      body,
    });
  } catch (err) {
    // 按 err.code 映射到合适的 HTTP 状态码
    if (err.code === 'BODY_TOO_LARGE') {
      sendJSON(res, { error: 'Request Entity Too Large', message: err.message }, 413);
    } else if (err.code === 'INVALID_JSON') {
      sendJSON(res, { error: 'Bad Request', message: err.message }, 400);
    } else {
      console.error('未处理错误：', err);
      sendJSON(res, { error: 'Internal Server Error' }, 500);
    }
  }
});

server.listen(PORT, () => {
  console.log(`JSON API 服务器已启动：http://localhost:${PORT}`);
  console.log('可用路由：');
  console.log('  GET  /api/ping    心跳');
  console.log('  POST /api/echo    回显 message 字段');
  console.log('  POST /api/form    解析表单');
  console.log('  POST /api/users   模拟创建用户（201）');
  console.log('  OPTIONS *         CORS 预检');
  console.log('按 Ctrl+C 停止');
});
