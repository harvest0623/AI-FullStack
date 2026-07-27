/**
 * multer-upload.js
 * ----------------------------------------------------------------
 * 用 multer 处理 multipart/form-data 文件上传，演示：
 *   1. diskStorage 磁盘存储（自定义 destination / filename）
 *   2. limits 限制文件大小（防内存耗尽）
 *   3. fileFilter 白名单 mimetype 校验（png/jpeg/webp）
 *   4. upload.single 单文件上传 → req.file
 *   5. upload.array 多文件上传 → req.files[]
 *   6. multer 错误统一抛给错误中间件（MULTER_ERROR 类型）
 *
 * 注意：multer 必须挂在校验中间件之前，否则 req.body / req.file 还没解析出来
 *
 * 运行：npm run multer   （node multer-upload.js）
 * ----------------------------------------------------------------
 */

const path = require('path');
const fs = require('fs');
const express = require('express');
const multer = require('multer');

const app = express();

// ----------------------------------------------------------------
// 1. 确保上传目录存在
// ----------------------------------------------------------------
const UPLOAD_DIR = path.join(__dirname, 'uploads');
if (!fs.existsSync(UPLOAD_DIR)) {
  fs.mkdirSync(UPLOAD_DIR, { recursive: true });
}

// ----------------------------------------------------------------
// 2. 配置磁盘存储
// ----------------------------------------------------------------
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, UPLOAD_DIR),
  filename: (req, file, cb) => {
    // 用 时间戳 + 随机串 + 原扩展名 避免重名
    const ext = path.extname(file.originalname);
    const base = `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
    cb(null, `${base}${ext}`);
  },
});

// ----------------------------------------------------------------
// 3. 创建 multer 实例（单文件 + 多文件各一份）
// ----------------------------------------------------------------
const ALLOWED_MIME = ['image/png', 'image/jpeg', 'image/webp'];
const MAX_SIZE = 5 * 1024 * 1024; // 5MB

const fileFilter = (req, file, cb) => {
  if (ALLOWED_MIME.includes(file.mimetype)) {
    cb(null, true);
  } else {
    // 注意：第二个参数 false 表示不接受此文件
    // 第一个参数传 Error，会被 multer 包装为 MulterError 或透传给 next(err)
    cb(new Error(`不支持的文件类型：${file.mimetype}，仅允许 png/jpeg/webp`), false);
  }
};

const upload = multer({
  storage,
  limits: { fileSize: MAX_SIZE },
  fileFilter,
});

// ----------------------------------------------------------------
// 4. 把 multer 中间件包装一层，把它的错误转成统一格式抛给错误中间件
//    （multer 出错时调用 next(err)，err.code 形如 LIMIT_FILE_SIZE / LIMIT_UNEXPECTED_FILE）
// ----------------------------------------------------------------
function wrapMulter(multerMiddleware) {
  return (req, res, next) => {
    multerMiddleware(req, res, (err) => {
      if (err) {
        // err 可能是 multer 的 MulterError，也可能是 fileFilter 抛的普通 Error
        return next({
          type: 'MULTER_ERROR',
          error: err,
        });
      }
      next();
    });
  };
}

// ----------------------------------------------------------------
// 5. 路由：单文件上传（头像）
// ----------------------------------------------------------------
app.post(
  '/api/upload/avatar',
  wrapMulter(upload.single('avatar')),
  (req, res) => {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: { code: 'NO_FILE', message: '未上传文件' },
      });
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

// ----------------------------------------------------------------
// 6. 路由：多文件上传（图集，最多 9 张）
// ----------------------------------------------------------------
app.post(
  '/api/upload/gallery',
  wrapMulter(upload.array('photos', 9)),
  (req, res) => {
    if (!req.files || req.files.length === 0) {
      return res.status(400).json({
        success: false,
        error: { code: 'NO_FILE', message: '未上传文件' },
      });
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

// ----------------------------------------------------------------
// 7. 静态托管上传目录（方便浏览器直接访问）
// ----------------------------------------------------------------
app.use('/uploads', express.static(UPLOAD_DIR));

// ----------------------------------------------------------------
// 8. 健康检查
// ----------------------------------------------------------------
app.get('/health', (req, res) => res.json({ success: true, message: 'multer-upload 服务运行中' }));

// ----------------------------------------------------------------
// 9. 启动服务（单独运行本文件时）
// ----------------------------------------------------------------
if (require.main === module) {
  const PORT = 3003;
  app.listen(PORT, () => {
    console.log(`[multer-upload] 服务已启动：http://localhost:${PORT}`);
    console.log('  POST /api/upload/avatar   单文件上传（字段名 avatar）');
    console.log('  POST /api/upload/gallery  多文件上传（字段名 photos，最多 9）');
    console.log('  GET  /uploads/<filename>  访问已上传文件');
    console.log('  GET  /health              健康检查');
    console.log('\n示例 curl：');
    console.log('  curl -X POST http://localhost:3003/api/upload/avatar \\');
    console.log('    -F "avatar=@./test.png"');
  });
}

// 导出供 server.js 组合使用
module.exports = { app, upload, wrapMulter, UPLOAD_DIR };
