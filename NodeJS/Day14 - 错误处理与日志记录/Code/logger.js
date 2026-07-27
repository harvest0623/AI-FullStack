// logger.js - winston 日志配置
// Console + DailyRotateFile, JSON 格式, 含 timestamp / requestId 上下文.
// 配合 request-id.js (挂 req.log) 与 app.js 使用.
//
// 设计要点:
//   - 文件日志用 JSON 格式 (便于 ELK/Loki 等聚合系统采集解析).
//   - 控制台日志用可读性更好的 printf + colorize (开发调试友好).
//   - error 级别单独一个轮转文件, 便于单独排查/告警.
//   - 按"天 + 大小"双维度轮转, 避免日志文件无限增长.
//   - 生产/开发环境采用不同默认级别.

'use strict';

const path = require('path');
const { createLogger, format, transports } = require('winston');
const DailyRotateFile = require('winston-daily-rotate-file');

const { combine, timestamp, printf, colorize, errors, json } = format;

const isProd = process.env.NODE_ENV === 'production';

// 控制台可读格式: 时间 [requestId] 级别: 消息 {上下文} 堆栈(如有)
const consolePrintf = printf((info) => {
  const {
    level, message, timestamp: ts, requestId, stack, ...meta
  } = info;
  const rid = requestId ? ` [${requestId}]` : '';
  const ctx = Object.keys(meta).length ? ` ${JSON.stringify(meta)}` : '';
  const errStack = stack ? `\n${stack}` : '';
  return `${ts}${rid} ${level}: ${message}${ctx}${errStack}`;
});

// 公共时间戳格式
const tsFormat = timestamp({ format: 'YYYY-MM-DD HH:mm:ss.SSS' });

// ---- 文件 transport: 全量日志 (info 及以上), JSON 格式 ----
const appRotateTransport = new DailyRotateFile({
  dirname: path.join(__dirname, 'logs'),
  filename: 'app-%DATE%.log',
  datePattern: 'YYYY-MM-DD',
  maxSize: '20m',      // 单文件最大 20MB
  maxFiles: '14d',     // 保留 14 天
  level: 'info',
  format: combine(tsFormat, errors({ stack: true }), json())
});

// ---- 文件 transport: 仅 error 级别, 单独文件便于告警/排查 ----
const errorRotateTransport = new DailyRotateFile({
  dirname: path.join(__dirname, 'logs'),
  filename: 'error-%DATE%.log',
  datePattern: 'YYYY-MM-DD',
  maxSize: '20m',
  maxFiles: '30d',     // 错误日志保留更久
  level: 'error',
  format: combine(tsFormat, errors({ stack: true }), json())
});

const logger = createLogger({
  level: isProd ? 'info' : 'debug',  // 生产关 debug, 开发开 debug
  defaultMeta: { service: 'day14-error-logging' },
  transports: [errorRotateTransport, appRotateTransport],
  // 未捕获的同步异常单独记录 (进程级兜底)
  exceptionHandlers: [
    new DailyRotateFile({
      dirname: path.join(__dirname, 'logs'),
      filename: 'exceptions-%DATE%.log',
      datePattern: 'YYYY-MM-DD',
      maxFiles: '30d'
    })
  ]
});

// 非生产环境额外加彩色控制台输出 (可读优先于机器可读)
if (!isProd) {
  logger.add(
    new transports.Console({
      level: 'debug',
      format: combine(colorize(), tsFormat, errors({ stack: true }), consolePrintf)
    })
  );
}

module.exports = logger;
