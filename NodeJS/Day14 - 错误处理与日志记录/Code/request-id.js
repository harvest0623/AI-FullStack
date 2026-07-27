// request-id.js - 请求 ID 中间件
// 为每个请求生成 uuid, 挂到 req.id, 注入响应头与 logger 上下文, 实现全链路追踪.
// 配合 logger.js / app.js 使用.

'use strict';

const { v4: uuidv4 } = require('uuid');
const logger = require('./logger');

/**
 * requestId 中间件职责:
 *  1. 优先读取请求头 X-Request-Id (便于上游网关/服务透传, 串联整条调用链),
 *     否则用 uuid v4 生成一个新 id.
 *  2. 挂到 req.id / req.requestId, 供后续中间件、路由、错误中间件读取.
 *  3. 写入响应头 X-Request-Id, 便于客户端/前端上报问题时提供该 id 快速定位日志.
 *  4. 创建带 requestId 默认字段的"子 logger"挂到 req.log,
 *     之后该请求所有日志自动带上 requestId, 贯穿全链路.
 *  5. 监听 res 'finish' 事件, 记录一条 access 日志 (含状态码与耗时).
 *
 * 必须在业务路由之前注册, 才能保证 req.log 可用.
 */
function requestId(req, res, next) {
  const id = req.get('X-Request-Id') || uuidv4();
  req.id = id;
  req.requestId = id;
  res.set('X-Request-Id', id);

  // child logger: 继承父级 transports/format, 自动带 requestId 字段
  req.log = logger.child({ requestId: id });

  // 记录请求开始时间 (用 hrtime 提高精度)
  const start = process.hrtime.bigint();

  res.on('finish', () => {
    const ms = Number(process.hrtime.bigint() - start) / 1e6;
    req.log.info('请求完成', {
      method: req.method,
      url: req.originalUrl,
      status: res.statusCode,
      durationMs: Number(ms.toFixed(2))
    });
  });

  next();
}

module.exports = requestId;
