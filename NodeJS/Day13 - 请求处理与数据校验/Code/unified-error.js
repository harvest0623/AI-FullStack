/**
 * unified-error.js
 * ----------------------------------------------------------------
 * 统一错误响应中间件，把来自不同来源的错误归一化为同一种 JSON 结构：
 *
 *   {
 *     "success": false,
 *     "error": {
 *       "code": "VALIDATION_ERROR",
 *       "message": "请求参数校验失败",
 *       "details": [{ "field": "email", "message": "邮箱格式不正确" }]
 *     }
 *   }
 *
 * 支持的错误来源：
 *   1. Joi 错误          → err.type === 'JOI_ERROR'
 *   2. express-validator → err.type === 'EXPRESS_VALIDATOR_ERROR'
 *   3. multer 错误       → err.type === 'MULTER_ERROR'
 *   4. 业务错误           → err.type === 'BUSINESS_ERROR'（自带 code/message）
 *   5. 其他未知错误       → 兜底 500
 *
 * 用法：在所有路由之后挂载 unifiedErrorHandler
 *
 * 运行：npm run error   （node unified-error.js）
 * ----------------------------------------------------------------
 */

const express = require('express');

// ----------------------------------------------------------------
// 1. 业务错误基类：service 层抛业务错误时用这个
// ----------------------------------------------------------------
class BusinessError extends Error {
  constructor(code, message, details = []) {
    super(message);
    this.type = 'BUSINESS_ERROR';
    this.code = code;
    this.details = details;
  }
}

// ----------------------------------------------------------------
// 2. 404 中间件：所有路由都没命中时
// ----------------------------------------------------------------
function notFoundHandler(req, res, next) {
  next({
    type: 'NOT_FOUND',
    message: `路由不存在：${req.method} ${req.originalUrl}`,
  });
}

// ----------------------------------------------------------------
// 3. 统一错误中间件（必须四个参数，Express 据此识别为错误中间件）
// ----------------------------------------------------------------
function unifiedErrorHandler(err, req, res, next) {
  // 默认值
  let status = 500;
  let code = 'INTERNAL_ERROR';
  let message = '服务器内部错误';
  let details = [];

  switch (err && err.type) {
    // ---- Joi 校验错误 ----
    case 'JOI_ERROR': {
      status = 422;
      code = 'VALIDATION_ERROR';
      message = '请求参数校验失败';
      details = (err.error.details || []).map((d) => ({
        // d.path 是数组，如 ['address', 'zip']
        field: Array.isArray(d.path) ? d.path.join('.') : d.path,
        message: d.message,
      }));
      break;
    }

    // ---- express-validator 校验错误 ----
    case 'EXPRESS_VALIDATOR_ERROR': {
      status = 422;
      code = 'VALIDATION_ERROR';
      message = '请求参数校验失败';
      details = (err.errors || []).map((e) => ({
        field: e.field || e.path,
        message: e.message,
      }));
      break;
    }

    // ---- multer 上传错误 ----
    case 'MULTER_ERROR': {
      status = 400;
      code = 'UPLOAD_ERROR';
      const multerErr = err.error || {};
      // MulterError 有 code 字段：LIMIT_FILE_SIZE / LIMIT_UNEXPECTED_FILE / LIMIT_FILE_COUNT 等
      if (multerErr.code === 'LIMIT_FILE_SIZE') {
        message = '文件大小超出限制';
      } else if (multerErr.code === 'LIMIT_UNEXPECTED_FILE') {
        message = `上传字段名不正确或文件数量超限（${multerErr.field || ''}）`;
      } else if (multerErr.code === 'LIMIT_FILE_COUNT') {
        message = '上传文件数量超出限制';
      } else {
        // fileFilter 抛的自定义 Error（没有 code）
        message = multerErr.message || '文件上传失败';
      }
      details = [{ field: multerErr.field || 'file', message }];
      break;
    }

    // ---- 业务错误 ----
    case 'BUSINESS_ERROR': {
      status = 400;
      code = err.code || 'BUSINESS_ERROR';
      message = err.message;
      details = err.details || [];
      break;
    }

    // ---- 404 ----
    case 'NOT_FOUND': {
      status = 404;
      code = 'NOT_FOUND';
      message = err.message;
      break;
    }

    // ---- 其他未知错误（兜底 500）----
    default: {
      status = 500;
      code = 'INTERNAL_ERROR';
      message = process.env.NODE_ENV === 'production'
        ? '服务器内部错误'
        : (err && err.message) || '未知错误';
      // 开发环境下附带堆栈，便于调试；生产环境绝不暴露
      if (process.env.NODE_ENV !== 'production') {
        details = [{ field: 'stack', message: err && err.stack ? err.stack : '' }];
      }
      break;
    }
  }

  // 统一输出
  res.status(status).json({
    success: false,
    error: {
      code,
      message,
      details,
    },
  });
}

// ----------------------------------------------------------------
// 4. 自测：搭一个最小应用验证所有错误分支
// ----------------------------------------------------------------
function buildDemoApp() {
  const app = express();
  app.use(express.json());

  // 故意抛业务错误
  app.get('/api/biz-error', (req, res, next) => {
    next(new BusinessError('USER_NOT_FOUND', '用户不存在', [{ field: 'userId', message: '该 ID 不存在' }]));
  });

  // 故意抛未知错误
  app.get('/api/crash', (req, res, next) => {
    next(new Error('数据库连接失败'));
  });

  // 404
  app.use(notFoundHandler);
  // 统一错误中间件必须放最后
  app.use(unifiedErrorHandler);
  return app;
}

// ----------------------------------------------------------------
// 5. 启动（单独运行本文件时）
// ----------------------------------------------------------------
if (require.main === module) {
  const app = buildDemoApp();
  const PORT = 3004;
  app.listen(PORT, () => {
    console.log(`[unified-error] 服务已启动：http://localhost:${PORT}`);
    console.log('  GET /api/biz-error  业务错误示例');
    console.log('  GET /api/crash      未知错误示例（500）');
    console.log('  GET /api/nope       404 示例');
  });
}

module.exports = { unifiedErrorHandler, notFoundHandler, BusinessError, buildDemoApp };
