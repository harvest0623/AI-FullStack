/**
 * http-server-typed.ts
 * 用 TypeScript 写一个原生 http 服务器：
 *   - IncomingMessage / ServerResponse 类型
 *   - 自定义 Request 接口扩展
 *   - 路由分发
 *
 * 运行：tsx http-server-typed.ts
 *      然后访问 http://localhost:3000/health 或 /users/123
 */

import http, { IncomingMessage, ServerResponse, Server } from 'node:http';

// ============================================================
// 1. 自定义 Request 接口：在原生 IncomingMessage 上扩展字段
// ============================================================

interface ParsedUrl {
  pathname: string;
  query: URLSearchParams;
}

interface AppRequest extends IncomingMessage {
  // 在中间件中挂上去的字段
  parsed?: ParsedUrl;
  body?: unknown;
}

// 自定义错误类型，便于路由层 throw 后被统一捕获
interface RouteContext {
  req: AppRequest;
  res: ServerResponse;
  params: Record<string, string>;
}

// ============================================================
// 2. 路由表类型化
// ============================================================

type Handler = (ctx: RouteContext) => Promise<void> | void;

interface Route {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  pattern: RegExp;
  paramNames: string[];
  handler: Handler;
}

const routes: Route[] = [];

function addRoute(
  method: Route['method'],
  pathPattern: string,
  handler: Handler,
): void {
  // 把 /users/:id 转成正则 + 参数名数组
  const paramNames: string[] = [];
  const regex = pathPattern.replace(/:([A-Za-z_]\w*)/g, (_, name: string) => {
    paramNames.push(name);
    return '([^/]+)';
  });
  routes.push({
    method,
    pattern: new RegExp(`^${regex}$`),
    paramNames,
    handler,
  });
}

// ============================================================
// 3. 注册几条路由
// ============================================================

addRoute('GET', '/health', async ({ res }) => {
  sendJson(res, 200, { status: 'ok', uptime: process.uptime() });
});

addRoute('GET', '/users/:id', async ({ res, params }) => {
  const id: string = params.id;
  sendJson(res, 200, { id, name: `User-${id}` });
});

addRoute('POST', '/echo', async ({ req, res }) => {
  // 这里仅做演示，真实场景需要按 stream 聚合
  const chunks: Buffer[] = [];
  for await (const chunk of req) {
    chunks.push(chunk as Buffer);
  }
  const bodyStr: string = Buffer.concat(chunks).toString('utf8');
  let parsed: unknown = bodyStr;
  try {
    parsed = JSON.parse(bodyStr);
  } catch {
    // 非 JSON 就原样回显
  }
  sendJson(res, 200, { received: parsed });
});

// ============================================================
// 4. 工具函数：JSON 响应
// ============================================================

function sendJson(res: ServerResponse, statusCode: number, payload: unknown): void {
  const body: string = JSON.stringify(payload);
  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(body),
  });
  res.end(body);
}

// ============================================================
// 5. 创建 Server：注意 req 的类型断言为 AppRequest
// ============================================================

const server: Server = http.createServer((req, res) => {
  // IncomingMessage 默认就是流，这里把 req 视作扩展后的 AppRequest
  const appReq = req as AppRequest;

  const url = new URL(appReq.url ?? '/', `http://${appReq.headers.host ?? 'localhost'}`);
  appReq.parsed = {
    pathname: url.pathname,
    query: url.searchParams,
  };

  const pathname: string = appReq.parsed.pathname;

  for (const route of routes) {
    if (route.method !== appReq.method) continue;
    const match = route.pattern.exec(pathname);
    if (!match) continue;

    const params: Record<string, string> = {};
    route.paramNames.forEach((name, i) => {
      params[name] = decodeURIComponent(match[i + 1] ?? '');
    });

    Promise.resolve(route.handler({ req: appReq, res, params })).catch((err: unknown) => {
      console.error('[route error]', err);
      sendJson(res, 500, { error: 'Internal Server Error' });
    });
    return;
  }

  sendJson(res, 404, { error: 'Not Found', path: pathname });
});

const PORT: number = Number(process.env.PORT ?? 3000);

server.listen(PORT, () => {
  console.log(`HTTP server listening on http://localhost:${PORT}`);
  console.log('Try:');
  console.log(`  curl http://localhost:${PORT}/health`);
  console.log(`  curl http://localhost:${PORT}/users/42`);
  console.log(`  curl -X POST http://localhost:${PORT}/echo -H "Content-Type: application/json" -d '{"a":1}`);
});
