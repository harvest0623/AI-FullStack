import app from './app';

const PORT = Number(process.env.PORT) || 3000;

app.listen(PORT, () => {
  console.log('─────────────────────────────────────────────────');
  console.log(`🚀 Day15 服务已启动: http://localhost:${PORT}`);
  console.log('─────────────────────────────────────────────────');
  console.log('');
  console.log('可用接口：');
  console.log('  GET    /health              健康检查');
  console.log('  GET    /api/articles        文章列表（支持 page/pageSize/keyword）');
  console.log('  GET    /api/articles/:id    文章详情');
  console.log('  POST   /api/articles        创建文章（需鉴权）');
  console.log('  PUT    /api/articles/:id    更新文章（需鉴权）');
  console.log('  DELETE /api/articles/:id    删除文章（需鉴权）');
  console.log('');
  console.log('可用 token：');
  console.log('  admin-token    管理员');
  console.log('  user-token     普通用户');
  console.log('');
  console.log('─────────────────────────────────────────────────');
  console.log('curl 测试命令示例：');
  console.log('─────────────────────────────────────────────────');
  console.log('');
  console.log('# 1. 健康检查');
  console.log(`curl http://localhost:${PORT}/health`);
  console.log('');
  console.log('# 2. 查询文章列表（默认前两篇文章已预置）');
  console.log(`curl "http://localhost:${PORT}/api/articles?page=1&pageSize=10"`);
  console.log('');
  console.log('# 3. 按关键词搜索');
  console.log(`curl "http://localhost:${PORT}/api/articles?keyword=NestJS"`);
  console.log('');
  console.log('# 4. 查询指定文章');
  console.log(`curl http://localhost:${PORT}/api/articles/1`);
  console.log('');
  console.log('# 5. 查询不存在的文章（演示 404 错误处理）');
  console.log(`curl http://localhost:${PORT}/api/articles/9999`);
  console.log('');
  console.log('# 6. 创建文章（带鉴权）');
  console.log(`curl -X POST http://localhost:${PORT}/api/articles \\
  -H "Authorization: Bearer admin-token" \\
  -H "Content-Type: application/json" \\
  -d '{"title":"第一篇新文章","content":"用 TS + Express 写后端"}'`);
  console.log('');
  console.log('# 7. 创建文章（无鉴权，演示 401 错误处理）');
  console.log(`curl -X POST http://localhost:${PORT}/api/articles \\
  -H "Content-Type: application/json" \\
  -d '{"title":"未授权的文章"}'`);
  console.log('');
  console.log('# 8. 创建文章（参数校验失败，演示 400 错误处理）');
  console.log(`curl -X POST http://localhost:${PORT}/api/articles \\
  -H "Authorization: Bearer admin-token" \\
  -H "Content-Type: application/json" \\
  -d '{"title":"","content":""}'`);
  console.log('');
  console.log('# 9. 更新文章');
  console.log(`curl -X PUT http://localhost:${PORT}/api/articles/1 \\
  -H "Authorization: Bearer admin-token" \\
  -H "Content-Type: application/json" \\
  -d '{"title":"修改后的标题"}'`);
  console.log('');
  console.log('# 10. 删除文章');
  console.log(`curl -X DELETE http://localhost:${PORT}/api/articles/2 \\
  -H "Authorization: Bearer admin-token"`);
  console.log('');
  console.log('# 11. 访问不存在的路由（演示 404 兜底）');
  console.log(`curl http://localhost:${PORT}/api/unknown`);
  console.log('');
});
