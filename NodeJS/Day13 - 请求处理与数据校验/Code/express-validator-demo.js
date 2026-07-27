/**
 * express-validator-demo.js
 * ----------------------------------------------------------------
 * 用 express-validator 的 checkSchema 校验文章创建接口，演示：
 *   1. checkSchema 声明式 schema（in: ['body'] 指定来源）
 *   2. notEmpty / isLength / isArray / isURL 等内置校验器
 *   3. custom 自定义校验器（tags 数组长度）
 *   4. trim / toLowerCase 等 sanitize 输入清洗
 *   5. validationResult 收集所有错误，统一抛给错误中间件
 *
 * 运行：npm run ev   （node express-validator-demo.js）
 * ----------------------------------------------------------------
 */

const express = require('express');
const { checkSchema, validationResult } = require('express-validator');

const app = express();
app.use(express.json());

// ----------------------------------------------------------------
// 1. 文章创建的 checkSchema
// ----------------------------------------------------------------
const articleCreateSchema = checkSchema({
  title: {
    in: ['body'],
    notEmpty: { errorMessage: '标题不可为空' },
    isLength: {
      options: { min: 2, max: 100 },
      errorMessage: '标题长度需在 2-100 字之间',
    },
    // sanitize：去首尾空格
    trim: true,
  },

  content: {
    in: ['body'],
    notEmpty: { errorMessage: '内容不可为空' },
    isLength: {
      options: { min: 10 },
      errorMessage: '内容至少 10 字',
    },
  },

  tags: {
    in: ['body'],
    isArray: { errorMessage: 'tags 必须是数组' },
    // 自定义校验器：数组长度 1-5，且每个元素长度 1-20
    custom: {
      options: (value) => {
        if (!Array.isArray(value)) return false;
        if (value.length < 1 || value.length > 5) return false;
        return value.every((t) => typeof t === 'string' && t.length >= 1 && t.length <= 20);
      },
      errorMessage: 'tags 需为 1-5 个元素，每个元素 1-20 字',
    },
  },

  // 可选字段：仅当传入时才校验
  cover: {
    in: ['body'],
    optional: { options: { nullable: true } },
    isURL: {
      options: { protocols: ['https'], require_protocol: true },
      errorMessage: 'cover 必须是合法的 https URL',
    },
  },

  // 可选字段：作者，trim + 转小写（sanitize 演示）
  author: {
    in: ['body'],
    optional: true,
    isLength: {
      options: { max: 30 },
      errorMessage: '作者名最多 30 字',
    },
    trim: true,
    toLowerCase: true,
  },
});

// ----------------------------------------------------------------
// 2. 错误收集中间件：把 express-validator 的错误统一抛给错误中间件
//    这样 controller 里就不必每个都写 if (!errors.isEmpty())
// ----------------------------------------------------------------
function handleValidationErrors(req, res, next) {
  const errors = validationResult(req);
  if (errors.isEmpty()) {
    return next();
  }
  // 把数组形式的错误转成 [{field, message}] 结构，方便统一中间件格式化
  const formatted = errors.array().map((e) => ({
    field: e.path,
    message: e.msg,
  }));
  next({
    type: 'EXPRESS_VALIDATOR_ERROR',
    errors: formatted,
  });
}

// ----------------------------------------------------------------
// 3. 路由：创建文章
// ----------------------------------------------------------------
app.post(
  '/api/articles',
  articleCreateSchema,
  handleValidationErrors,
  (req, res) => {
    // 此时 req.body 已经过 sanitize（trim / toLowerCase）
    const article = {
      ...req.body,
      id: Date.now(),
      createdAt: new Date().toISOString(),
    };
    res.json({
      success: true,
      data: article,
      message: '文章创建成功（演示用，未真实写库）',
    });
  }
);

// ----------------------------------------------------------------
// 4. 健康检查
// ----------------------------------------------------------------
app.get('/health', (req, res) => res.json({ success: true, message: 'express-validator 服务运行中' }));

// ----------------------------------------------------------------
// 5. 启动服务（单独运行本文件时）
// ----------------------------------------------------------------
if (require.main === module) {
  const PORT = 3002;
  app.listen(PORT, () => {
    console.log(`[express-validator] 服务已启动：http://localhost:${PORT}`);
    console.log('  POST /api/articles  创建文章（checkSchema 校验）');
    console.log('  GET  /health        健康检查');
    console.log('\n示例 curl：');
    console.log('  curl -X POST http://localhost:3002/api/articles \\');
    console.log('    -H "Content-Type: application/json" \\');
    console.log('    -d \'{"title":"我的第一篇文章","content":"这是至少十个字的内容","tags":["node","express"]}\'');
  });
}

// 导出供 server.js 组合使用
module.exports = { app, articleCreateSchema, handleValidationErrors };
