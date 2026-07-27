/**
 * server.js
 * ----------------------------------------------------------------
 * Day13 整合应用：把 Joi 校验、express-validator 校验、multer 上传、
 * 统一错误响应组合成一个完整服务，演示“请求处理完整链路 + 分层校验”。
 *
 * 启动：
 *   npm install        # 安装 express joi express-validator multer
 *   npm start          # 等同于 node server.js
 *
 * 路由总览：
 *   GET  /health                   健康检查
 *   POST /api/register             用户注册（Joi 校验 body）
 *   GET  /api/users                用户查询（Joi 校验 query，演示类型转换）
 *   PUT  /api/users/:id            用户更新（Joi 校验 params + body）
 *   POST /api/articles             创建文章（express-validator checkSchema）
 *   POST /api/upload/avatar        单文件上传（multer）
 *   POST /api/upload/gallery       多文件上传（multer）
 *   POST /api/avatar               文件上传 + 字段校验组合（multer + express-validator）
 *   GET  /api/biz-error            业务错误示例（service 层抛 BusinessError）
 *
 * ----------------------------------------------------------------
 */

const path = require('path');
const fs = require('fs');
const express = require('express');
const Joi = require('joi');
const { body, validationResult } = require('express-validator');

// 复用各模块导出的能力
const { registerSchema, validate } = require('./joi-validation');
const { articleCreateSchema, handleValidationErrors } = require('./express-validator-demo');
const { upload, wrapMulter, UPLOAD_DIR } = require('./multer-upload');
const { unifiedErrorHandler, notFoundHandler, BusinessError } = require('./unified-error');

const app = express();

// 确保上传目录存在
if (!fs.existsSync(UPLOAD_DIR)) {
  fs.mkdirSync(UPLOAD_DIR, { recursive: true });
}

// ----------------------------------------------------------------
// 全局中间件：日志（演示中间件链顺序）
// ----------------------------------------------------------------
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.originalUrl} → ${res.statusCode} (${Date.now() - start}ms)`);
  });
  next();
});

// ----------------------------------------------------------------
// 请求体解析中间件（必须在所有需要 req.body 的路由之前）
// ----------------------------------------------------------------
app.use(express.json({ limit: '1mb' }));
app.use(express.urlencoded({ extended: true, limit: '1mb' }));

// 静态托管上传目录
app.use('/uploads', express.static(UPLOAD_DIR));

// ----------------------------------------------------------------
// 健康检查
// ----------------------------------------------------------------
app.get('/health', (req, res) => {
  res.json({ success: true, message: 'Day13 整合服务运行中', time: new Date().toISOString() });
});

// ================================================================
// 一、Joi 校验演示
// ================================================================

// 1.1 用户注册（body 校验）
app.post(
  '/api/register',
  validate(registerSchema, 'body'),
  (req, res) => {
    res.json({
      success: true,
      data: { id: Date.now(), ...req.body, createdAt: new Date().toISOString() },
      message: '注册成功（Joi 校验通过）',
    });
  }
);

// 1.2 用户查询（query 校验，演示类型转换：page/limit 字符串 → 数字）
const userQuerySchema = Joi.object({
  page: Joi.number().integer().min(1).default(1),
  limit: Joi.number().integer().min(1).max(100).default(10),
  keyword: Joi.string().max(50).optional().allow(''),
  active: Joi.boolean().default(true),
}).options({ stripUnknown: true, abortEarly: false });

app.get(
  '/api/users',
  validate(userQuerySchema, 'query'),
  (req, res) => {
    // 注意：req.query 经过 Joi 后已是 number / boolean，不再是字符串
    res.json({
      success: true,
      data: {
        query: req.query,
        types: {
          page: typeof req.query.page,       // 'number'
          limit: typeof req.query.limit,     // 'number'
          active: typeof req.query.active,   // 'boolean'
        },
      },
      message: '查询成功（Joi 已做类型转换）',
    });
  }
);

// 1.3 用户更新（params + body 同时校验）
const userIdSchema = Joi.object({
  id: Joi.string().pattern(/^\d+$/).required().messages({
    'string.pattern.base': 'id 必须是纯数字字符串',
    'any.required': '缺少路径参数 id',
  }),
}).options({ stripUnknown: true, abortEarly: false });

const userUpdateSchema = Joi.object({
  email: Joi.string().email().optional(),
  age: Joi.number().integer().min(18).max(100).optional(),
}).options({ stripUnknown: true, abortEarly: false }).min(1).messages({
  'object.min': '至少需要更新一个字段',
});

app.put(
  '/api/users/:id',
  validate(userIdSchema, 'params'),
  validate(userUpdateSchema, 'body'),
  (req, res) => {
    res.json({
      success: true,
      data: { id: req.params.id, patch: req.body },
      message: '更新成功（params + body 双重校验通过）',
    });
  }
);

// ================================================================
// 二、express-validator 校验演示
// ================================================================

// 2.1 创建文章（checkSchema）
app.post(
  '/api/articles',
  articleCreateSchema,
  handleValidationErrors,
  (req, res) => {
    res.json({
      success: true,
      data: { id: Date.now(), ...req.body, createdAt: new Date().toISOString() },
      message: '文章创建成功（express-validator 校验通过）',
    });
  }
);

// ================================================================
// 三、multer 上传演示
// ================================================================

// 3.1 单文件上传
app.post(
  '/api/upload/avatar',
  wrapMulter(upload.single('avatar')),
  (req, res) => {
    if (!req.file) {
      throw new BusinessError('NO_FILE', '未上传文件', [{ field: 'avatar', message: '请选择文件' }]);
    }
    res.json({
      success: true,
      data: {
        url: `/uploads/${req.file.filename}`,
        originalName: req.file.originalname,
        size: req.file.size,
        mimetype: req.file.mimetype,
      },
    });
  }
);

// 3.2 多文件上传
app.post(
  '/api/upload/gallery',
  wrapMulter(upload.array('photos', 9)),
  (req, res) => {
    if (!req.files || req.files.length === 0) {
      throw new BusinessError('NO_FILE', '未上传文件', [{ field: 'photos', message: '请至少选择一个文件' }]);
    }
    res.json({
      success: true,
      data: req.files.map((f) => ({
        url: `/uploads/${f.filename}`,
        originalName: f.originalname,
        size: f.size,
        mimetype: f.mimetype,
      })),
    });
  }
);

// 3.3 组合：multer + express-validator（上传头像 + caption 文本字段）
//     注意顺序：multer 必须在 express-validator 之前，否则拿不到 req.body.caption
app.post(
  '/api/avatar',
  wrapMulter(upload.single('avatar')),
  [
    body('caption')
      .trim()
      .notEmpty().withMessage('caption 不可为空')
      .isLength({ max: 50 }).withMessage('caption 最多 50 字'),
  ],
  (req, res, next) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      const formatted = errors.array().map((e) => ({ field: e.path, message: e.msg }));
      return next({ type: 'EXPRESS_VALIDATOR_ERROR', errors: formatted });
    }
    if (!req.file) {
      throw new BusinessError('NO_FILE', '未上传头像文件', [{ field: 'avatar', message: '请选择文件' }]);
    }
    res.json({
      success: true,
      data: {
        url: `/uploads/${req.file.filename}`,
        caption: req.body.caption,
        originalName: req.file.originalname,
      },
      message: '头像 + 文本字段组合上传成功',
    });
  }
);

// ================================================================
// 四、业务错误示例（演示 service 层错误也走统一中间件）
// ================================================================
app.get('/api/biz-error', (req, res, next) => {
  // 模拟 service 层抛出业务错误
  next(new BusinessError('USER_NOT_FOUND', '用户不存在', [{ field: 'userId', message: '该 ID 不存在' }]));
});

// ================================================================
// 错误兜底：404 + 统一错误中间件（必须放最后）
// ================================================================
app.use(notFoundHandler);
app.use(unifiedErrorHandler);

// ----------------------------------------------------------------
// 启动服务
// ----------------------------------------------------------------
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log('============================================================');
  console.log(`  Day13 整合服务已启动：http://localhost:${PORT}`);
  console.log('============================================================');
  console.log(`
可用接口：
  GET  /health                 健康检查
  POST /api/register           用户注册（Joi）
  GET  /api/users              用户查询（Joi 校验 query + 类型转换）
  PUT  /api/users/:id          用户更新（Joi params + body）
  POST /api/articles           创建文章（express-validator checkSchema）
  POST /api/upload/avatar      单文件上传（multer）
  POST /api/upload/gallery     多文件上传（multer）
  POST /api/avatar             文件 + 字段组合上传（multer + express-validator）
  GET  /api/biz-error          业务错误示例
`);
  console.log('curl 测试命令见源码注释。\n');
});

/*
 * ================================================================
 * curl 测试命令（成功 + 失败用例）
 * ================================================================
 *
 * ---------- 1. 用户注册（Joi） ----------
 *
 * # 成功
 * curl -X POST http://localhost:3000/api/register \
 *   -H "Content-Type: application/json" \
 *   -d '{"username":"alice","email":"a@b.com","password":"abc12345","age":20,"tags":["node","express"]}'
 *
 * # 失败：密码强度不足（缺字母）
 * curl -X POST http://localhost:3000/api/register \
 *   -H "Content-Type: application/json" \
 *   -d '{"username":"alice","email":"a@b.com","password":"12345678"}'
 * # 期望：422，details 含 password 字段，message 提示需含字母和数字
 *
 * # 失败：未知字段被 stripUnknown 丢弃（__proto__ 不会污染）
 * curl -X POST http://localhost:3000/api/register \
 *   -H "Content-Type: application/json" \
 *   -d '{"username":"alice","email":"a@b.com","password":"abc12345","__proto__":{"isAdmin":true},"extra":"x"}'
 * # 期望：200，响应 data 中不包含 extra 和 isAdmin
 *
 * # 失败：多字段同时错（abortEarly: false 一次性返回所有错误）
 * curl -X POST http://localhost:3000/api/register \
 *   -H "Content-Type: application/json" \
 *   -d '{"username":"a","email":"bad","password":"1","age":5}'
 * # 期望：422，details 含 username/email/password/age 四条
 *
 * ---------- 2. 用户查询（Joi 校验 query + 类型转换） ----------
 *
 * # 成功：观察响应中 types.page/limit/active 都是 number/boolean
 * curl "http://localhost:3000/api/users?page=2&limit=20&active=false"
 *
 * # 失败：limit 超过 100
 * curl "http://localhost:3000/api/users?limit=999"
 *
 * ---------- 3. 用户更新（Joi params + body 双重校验） ----------
 *
 * # 成功
 * curl -X PUT http://localhost:3000/api/users/123 \
 *   -H "Content-Type: application/json" \
 *   -d '{"age":25}'
 *
 * # 失败：id 非数字
 * curl -X PUT http://localhost:3000/api/users/abc \
 *   -H "Content-Type: application/json" \
 *   -d '{"age":25}'
 * # 期望：422，details 含 id 字段
 *
 * # 失败：body 为空对象（object.min）
 * curl -X PUT http://localhost:3000/api/users/123 \
 *   -H "Content-Type: application/json" \
 *   -d '{}'
 *
 * ---------- 4. 创建文章（express-validator checkSchema） ----------
 *
 * # 成功
 * curl -X POST http://localhost:3000/api/articles \
 *   -H "Content-Type: application/json" \
 *   -d '{"title":"我的第一篇文章","content":"这是至少十个字的内容","tags":["node","express"],"cover":"https://example.com/c.png"}'
 *
 * # 失败：tags 为空数组（custom 校验）
 * curl -X POST http://localhost:3000/api/articles \
 *   -H "Content-Type: application/json" \
 *   -d '{"title":"测试","content":"内容超过十个字了哈哈哈","tags":[]}'
 * # 期望：422，message 提示 tags 需 1-5 个
 *
 * # 失败：cover 非 https
 * curl -X POST http://localhost:3000/api/articles \
 *   -H "Content-Type: application/json" \
 *   -d '{"title":"测试","content":"内容超过十个字了哈哈哈","tags":["a"],"cover":"http://insecure.com"}'
 * # 期望：422，message 提示 cover 必须是 https
 *
 * ---------- 5. 单文件上传（multer） ----------
 *
 * # 成功（需准备 test.png）
 * curl -X POST http://localhost:3000/api/upload/avatar \
 *   -F "avatar=@./test.png"
 *
 * # 失败：文件类型不支持
 * curl -X POST http://localhost:3000/api/upload/avatar \
 *   -F "avatar=@./test.txt"
 * # 期望：400，code=UPLOAD_ERROR
 *
 * # 失败：文件超 5MB（准备一个大文件）
 * curl -X POST http://localhost:3000/api/upload/avatar \
 *   -F "avatar=@./big.png"
 * # 期望：400，message=文件大小超出限制
 *
 * ---------- 6. 多文件上传（multer） ----------
 *
 * # 成功（多张）
 * curl -X POST http://localhost:3000/api/upload/gallery \
 *   -F "photos=@./a.png" -F "photos=@./b.png"
 *
 * # 失败：超过 9 张
 * # （略，自行构造 10 张图片）
 *
 * ---------- 7. 组合上传：文件 + 文本字段 ----------
 *
 * # 成功
 * curl -X POST http://localhost:3000/api/avatar \
 *   -F "avatar=@./test.png" -F "caption=我的头像"
 *
 * # 失败：caption 超长
 * curl -X POST http://localhost:3000/api/avatar \
 *   -F "avatar=@./test.png" -F "caption=$(python -c 'print("a"*60)')"
 * # 期望：422，message=caption 最多 50 字
 *
 * # 失败：caption 为空
 * curl -X POST http://localhost:3000/api/avatar \
 *   -F "avatar=@./test.png" -F "caption="
 *
 * ---------- 8. 业务错误示例 ----------
 *
 * curl http://localhost:3000/api/biz-error
 * # 期望：400，code=USER_NOT_FOUND
 *
 * ---------- 9. 404 ----------
 *
 * curl http://localhost:3000/api/nope
 * # 期望：404，code=NOT_FOUND
 *
 * ================================================================
 */
