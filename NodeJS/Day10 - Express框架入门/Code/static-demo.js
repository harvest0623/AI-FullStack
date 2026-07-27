// static-demo.js - express.static 静态文件服务演示
// 运行: npm run static   或   node static-demo.js
// 访问: http://localhost:3002

const express = require('express');
const path = require('path');
const app = express();

// ----------------------------------------------------------------
// express.static(root, options) 把 root 目录下的文件映射为可访问 URL
// ----------------------------------------------------------------

// 推荐做法（需先创建 public 目录并放入 index.html 等文件）：
//   app.use(express.static(path.join(__dirname, 'public')));
//   访问 http://localhost:3002/index.html 即可读取 public/index.html

// 挂载到虚拟路径前缀：
//   app.use('/static', express.static(path.join(__dirname, 'public')));
//   访问 http://localhost:3002/static/index.html

// 为保证本文件可独立运行（无需额外创建 public 目录），
// 这里临时把 Code 目录本身作为静态根，便于演示访问 app.js / package.json
app.use(express.static(__dirname));

app.get('/', (req, res) => {
  res.type('text/html').send(
    '<h1>静态文件服务已启动</h1>' +
    '<p>尝试访问以下文件:</p>' +
    '<ul>' +
    '<li><a href="/app.js">/app.js</a></li>' +
    '<li><a href="/package.json">/package.json</a></li>' +
    '<li><a href="/server.js">/server.js</a></li>' +
    '</ul>'
  );
});

const PORT = 3002;
app.listen(PORT, () => {
  console.log(`Static demo running at http://localhost:${PORT}`);
});

/* ===================== 说明 =====================
1. express.static 是 Express 唯一内置的“功能型”中间件，
   基于 serve-static 实现，会自动处理 ETag、Last-Modified、Range（断点续传）等。

2. 常用 options：
   {
     index: 'index.html',   // 默认首页文件，设为 false 可禁用
     maxAge: 0,             // 浏览器缓存时长（毫秒）
     etag: true,            // 是否生成 ETag
     lastModified: true,    // 是否使用 Last-Modified 头
     setHeaders: (res, path) => { ... }  // 自定义响应头
   }

3. 生产环境建议：
   - 静态资源交由 CDN 或 nginx 提供，Express 仅处理动态 API；
   - 若必须用 Express 提供静态资源，开启压缩（compression）与缓存。

4. 安全提示：不要把包含敏感信息（.env、密钥）的目录直接作为静态根。
================================================ */
