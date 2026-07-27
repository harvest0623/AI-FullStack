/**
 * Day12 - RESTful API 服务入口
 *
 * 职责：
 *   1. 创建 Express 应用，注册全局中间件
 *   2. 挂载文章路由到 /api/v1/articles
 *   3. 提供 404 兜底与统一错误处理中间件
 *
 * 启动：npm start  或  node server.js
 *
 * 完整 curl 测试命令见文件末尾注释。
 */

const express = require('express');
const articlesRouter = require('./articles-router');

const app = express();
const PORT = process.env.PORT || 3000;

// ---------------------------------------------------------------------------
// 全局中间件
// ---------------------------------------------------------------------------

// 解析 JSON 请求体 → req.body
// 限制大小 1mb，防止超大 body 拖垮服务
app.use(express.json({ limit: '1mb' }));

// 简易请求日志中间件：记录时间、方法、路径
app.use((req, res, next) => {
  const time = new Date().toISOString();
  console.log(`[${time}] ${req.method} ${req.originalUrl}`);
  next();
});

// ---------------------------------------------------------------------------
// 路由挂载
// ---------------------------------------------------------------------------

// 健康检查（无需鉴权，供运维/监控探活）
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
  });
});

// 文章资源路由（URI 版本化：/api/v1）
app.use('/api/v1/articles', articlesRouter);

// ---------------------------------------------------------------------------
// 404 兜底处理
// 放在所有路由之后，匹配不到任何路由时触发
// ---------------------------------------------------------------------------
app.use((req, res) => {
  res.status(404).json({
    code: 404,
    message: `路由不存在: ${req.method} ${req.originalUrl}`,
    data: null,
  });
});

// ---------------------------------------------------------------------------
// 统一错误处理中间件（四参数，必须放在最后）
// 捕获所有 next(err) 转发过来的错误，以及异步包装器捕获的 rejection
// ---------------------------------------------------------------------------
// eslint-disable-next-line no-unused-vars
app.use((err, req, res, next) => {
  console.error('未捕获错误:', err);

  // JSON 解析失败（请求体不是合法 JSON）
  if (err.type === 'entity.parse.failed') {
    return res.status(400).json({
      code: 400,
      message: '请求体 JSON 格式错误',
      data: null,
    });
  }

  // 请求体超过限制大小
  if (err.type === 'entity.too.large') {
    return res.status(413).json({
      code: 413,
      message: '请求体过大（超过 1mb 限制）',
      data: null,
    });
  }

  // 其它未预期错误统一返回 500
  // 注意：生产环境不应把 err.message 直接暴露给客户端（可能含敏感信息）
  return res.status(500).json({
    code: 500,
    message: '服务器内部错误',
    data: null,
  });
});

// ---------------------------------------------------------------------------
// 启动服务
// ---------------------------------------------------------------------------
app.listen(PORT, () => {
  console.log(`\n🚀 Server running at http://localhost:${PORT}`);
  console.log(`📋 文章 API:    http://localhost:${PORT}/api/v1/articles`);
  console.log(`❤️  健康检查:    http://localhost:${PORT}/health\n`);
});

// ===========================================================================
// 完整 curl 测试命令（请先启动服务：npm start）
// 建议按顺序执行，后面的测试依赖前面的创建/更新操作
// ===========================================================================
//
// ─── 0. 健康检查 ──────────────────────────────────────────────────────────
// curl http://localhost:3000/health
//
//
// ─── 1. 查询列表 ──────────────────────────────────────────────────────────
//
// 1.1 获取文章列表（默认分页 page=1, pageSize=10）
// curl http://localhost:3000/api/v1/articles
//
// 1.2 分页查询（第 1 页，每页 2 条）
// curl "http://localhost:3000/api/v1/articles?page=1&pageSize=2"
//
// 1.3 分页查询（第 2 页，每页 2 条）
// curl "http://localhost:3000/api/v1/articles?page=2&pageSize=2"
//
// 1.4 关键词搜索（标题或内容包含 "REST"）
// curl "http://localhost:3000/api/v1/articles?keyword=REST"
//
// 1.5 按作者过滤
// curl "http://localhost:3000/api/v1/articles?author=Alice"
//
// 1.6 排序（按创建时间倒序）
// curl "http://localhost:3000/api/v1/articles?sort=createdAt:desc"
//
// 1.7 组合查询（关键词 + 排序 + 分页）
// curl "http://localhost:3000/api/v1/articles?keyword=node&sort=createdAt:desc&page=1&pageSize=5"
//
//
// ─── 2. 查询详情 ──────────────────────────────────────────────────────────
//
// 2.1 获取单篇文章（成功）
// curl http://localhost:3000/api/v1/articles/1
//
// 2.2 获取不存在的文章（404）
// curl http://localhost:3000/api/v1/articles/999
//
//
// ─── 3. 创建文章（POST）──────────────────────────────────────────────────
//
// 3.1 创建文章（成功，返回 201）
// curl -X POST http://localhost:3000/api/v1/articles \
//   -H "Content-Type: application/json" \
//   -d '{"title":"新文章标题","content":"这是新文章的内容","author":"Dave","tags":["new","test"]}'
//
// 3.2 创建文章 - 缺少必填字段（422）
// curl -X POST http://localhost:3000/api/v1/articles \
//   -H "Content-Type: application/json" \
//   -d '{"author":"Dave"}'
//
// 3.3 创建文章 - JSON 格式错误（400）
// curl -X POST http://localhost:3000/api/v1/articles \
//   -H "Content-Type: application/json" \
//   -d '{invalid json}'
//
// 3.4 创建文章 - 不传 body（422）
// curl -X POST http://localhost:3000/api/v1/articles
//
//
// ─── 4. 全量更新（PUT）───────────────────────────────────────────────────
//
// 4.1 全量更新（成功，返回 200）—— 所有字段都会被覆盖
// curl -X PUT http://localhost:3000/api/v1/articles/1 \
//   -H "Content-Type: application/json" \
//   -d '{"title":"更新后的标题","content":"更新后的内容","author":"Alice2","tags":["updated"]}'
//
// 4.2 全量更新 - 缺少必填字段（422）—— PUT 要求全量
// curl -X PUT http://localhost:3000/api/v1/articles/1 \
//   -H "Content-Type: application/json" \
//   -d '{"title":"仅标题"}'
//
// 4.3 全量更新不存在的文章（404）
// curl -X PUT http://localhost:3000/api/v1/articles/999 \
//   -H "Content-Type: application/json" \
//   -d '{"title":"x","content":"y"}'
//
//
// ─── 5. 部分更新（PATCH）─────────────────────────────────────────────────
//
// 5.1 部分更新（成功，只改 title，其它字段不变）
// curl -X PATCH http://localhost:3000/api/v1/articles/1 \
//   -H "Content-Type: application/json" \
//   -d '{"title":"仅修改标题"}'
//
// 5.2 部分更新多个字段
// curl -X PATCH http://localhost:3000/api/v1/articles/1 \
//   -H "Content-Type: application/json" \
//   -d '{"tags":["patched","demo"],"author":"Eve"}'
//
// 5.3 部分更新 - 不传可更新字段（422）
// curl -X PATCH http://localhost:3000/api/v1/articles/1 \
//   -H "Content-Type: application/json" \
//   -d '{"id":999}'
//
// 5.4 部分更新不存在的文章（404）
// curl -X PATCH http://localhost:3000/api/v1/articles/999 \
//   -H "Content-Type: application/json" \
//   -d '{"title":"x"}'
//
//
// ─── 6. 删除文章（DELETE）────────────────────────────────────────────────
//
// 6.1 删除文章（成功，返回 204 无内容，加 -i 查看状态码）
// curl -i -X DELETE http://localhost:3000/api/v1/articles/1
//
// 6.2 删除不存在的文章（404）
// curl -i -X DELETE http://localhost:3000/api/v1/articles/999
//
// 6.3 重复删除（幂等性验证）—— 上一步已删，再删应 404
// curl -i -X DELETE http://localhost:3000/api/v1/articles/1
//
//
// ─── 7. 幂等性验证 ─────────────────────────────────────────────────────────
//
// 7.1 PUT 幂等：连续执行两次相同 PUT，结果一致（updatedAt 会变，业务字段不变）
// curl -X PUT http://localhost:3000/api/v1/articles/2 \
//   -H "Content-Type: application/json" \
//   -d '{"title":"幂等测试","content":"重复执行结果不变","author":"Test","tags":["idempotent"]}'
// curl -X PUT http://localhost:3000/api/v1/articles/2 \
//   -H "Content-Type: application/json" \
//   -d '{"title":"幂等测试","content":"重复执行结果不变","author":"Test","tags":["idempotent"]}'
//
//
// ─── 8. 404 与错误处理 ─────────────────────────────────────────────────────
//
// 8.1 访问不存在的路由（404）
// curl http://localhost:3000/api/v1/unknown
//
// 8.2 对 articles 集合用不支持的 HTTP 方法（404）
// curl -X PUT http://localhost:3000/api/v1/articles
