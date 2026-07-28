/**
 * Day17 - mongoose Model CRUD 与 populate 关联查询演示
 *
 * 演示内容：
 *   1. 连接 MongoDB（mongoose.connect + 连接事件监听）
 *   2. create / find / findById / findByIdAndUpdate / updateOne / deleteOne
 *   3. populate 关联查询（Article → User）
 *   4. 聚合 aggregate 简述（按作者统计文章数）
 *
 * ----------------------------------------------------------------------------
 * 环境准备（运行前必读）：
 *
 * 1) 本机需安装并启动 MongoDB 服务（4.4+ 或 6.x/7.x 均可）。
 *    - Windows: 下载 MongoDB Community Server，或用 Docker：
 *        docker run -d --name mongo -p 27017:27017 mongo:7
 *    - macOS:   brew tap mongodb/brew && brew install mongodb-community
 *               brew services start mongodb-community
 *    - Linux:   参考 docs.mongodb.com 手册
 *
 * 2) MongoDB 默认无密码即可连本机，URI 通常为：
 *        mongodb://127.0.0.1:27017/day17_demo
 *
 * 3) 安装依赖： npm install
 * 4) 运行：     node mongoose-crud.js
 *
 * 若本机没有 MongoDB，运行会打印友好错误并退出，不会崩溃。
 * ----------------------------------------------------------------------------
 */

const { mongoose, User, Article } = require('./mongoose-model');

const MONGO_URI = process.env.MONGO_URI || 'mongodb://127.0.0.1:27017/day17_demo';

// ---------------------------------------------------------------------------
// 1. 连接 MongoDB + 监听连接事件
// ---------------------------------------------------------------------------
// mongoose 6+ 默认已启用 useNewUrlParser / useUnifiedTopology，无需再传这些选项。
// 连接池大小通过 maxPoolSize（旧名 poolSize）配置，默认 100。
async function connect() {
  // 监听连接事件，便于排查问题
  mongoose.connection.on('connected', () => console.log('[Mongo] 已连接'));
  mongoose.connection.on('disconnected', () => console.warn('[Mongo] 连接断开'));
  mongoose.connection.on('error', (err) => console.error('[Mongo] 连接错误:', err.message));

  try {
    await mongoose.connect(MONGO_URI, {
      // 连接池大小：Node 单进程建议 10~50，按并发量调整
      maxPoolSize: 20,
      serverSelectionTimeoutMS: 5000, // 5s 内连不上就报错，避免长时间挂起
    });
    console.log('[Mongo] 连接成功 ✓');
  } catch (err) {
    console.error('[Mongo] 连接失败，请确认本地 MongoDB 服务已启动（默认端口 27017）。');
    console.error('  错误名:', err.name);
    console.error('  原因:', err.message);
    console.error('\n  快速方案：docker run -d --name mongo -p 27017:27017 mongo:7');
    process.exit(1);
  }
}

// ---------------------------------------------------------------------------
// 2. CRUD 演示
// ---------------------------------------------------------------------------
async function crudDemo() {
  // 清空旧数据，便于重复运行
  await User.deleteMany({});
  await Article.deleteMany({});

  // ---- Create：Model.create(doc) 等价于 new Model(doc).save() ----
  const alice = await User.create({
    username: 'alice',
    email: 'Alice@Example.com', // 会自动 lowercase
    role: 'admin',
    age: 28,
  });
  const bob = await User.create({
    username: 'bob',
    email: 'bob@example.com',
    role: 'editor',
    age: 35,
  });

  // 创建文章，author 引用 alice/bob 的 _id
  const a1 = await Article.create({ title: 'Node 入门', content: '...', author: alice._id, tags: ['node', 'backend'] });
  const a2 = await Article.create({ title: 'Express 指南', content: '...', author: alice._id, tags: ['express'] });
  const a3 = await Article.create({ title: 'Mongo 实战', content: '...', author: bob._id, tags: ['mongo', 'db'] });

  console.log('[Create] alice._id =', alice._id.toString());

  // ---- Read：find / findOne / findById ----
  const allArticles = await Article.find().sort({ createdAt: -1 });
  console.log('[find] 文章数 =', allArticles.length);

  // ---- populate：把 author 的 ObjectId 替换成完整 User 文档（类似 JOIN）----
  const withAuthor = await Article.findById(a1._id).populate('author', 'username role -_id');
  // 第二参数 'username role -_id' 表示只取 username/role，排除 _id
  console.log('[populate] 文章作者 =', withAuthor.author.username, '/', withAuthor.author.role);

  // 多层 populate 也可：Article.author 是 User，可继续 populate
  // await Article.find().populate({ path: 'author', populate: { path: 'friends' } });

  // ---- Update：findByIdAndUpdate（返回更新后文档）/ updateOne（返回写入结果）----
  const updated = await Article.findByIdAndUpdate(
    a1._id,
    { $inc: { viewCount: 5 }, $push: { tags: 'popular' } },
    { new: true } // 返回更新后的文档（默认返回旧文档）
  );
  console.log('[update] viewCount =', updated.viewCount, ', tags =', updated.tags);

  // updateOne 不返回文档，只返回 { acknowledged, modifiedCount, ... }
  const updRes = await Article.updateOne({ _id: a2._id }, { $set: { content: 'updated content' } });
  console.log('[updateOne] modifiedCount =', updRes.modifiedCount);

  // findOneAndUpdate：按条件查找并更新（无 id 时常用）
  await Article.findOneAndUpdate({ title: 'Mongo 实战' }, { $inc: { viewCount: 1 } });

  // ---- 软删除：仅置 deleted=true（Schema 的 pre-find 钩子会自动过滤）----
  await Article.findByIdAndUpdate(a3._id, { deleted: true });
  const visible = await Article.find();
  console.log('[软删除] 可见文章数 =', visible.length, '（应为 2，被软删的不出现在普通查询中）');

  // 显式查询包含软删除的文档：需主动传 deleted: true 覆盖钩子默认行为
  const trashed = await Article.find({ deleted: true });
  console.log('[软删除] 回收站文章数 =', trashed.length);

  // ---- 硬删除：deleteOne 真正移除文档 ----
  await Article.deleteOne({ _id: a2._id });
  console.log('[deleteOne] 已硬删除 a2');

  // ---- 聚合 aggregate：按作者统计文章数 ----
  // 管道：$match 过滤 → $group 按 author 聚合 → $lookup 关联 User → $project 投影
  const stats = await Article.aggregate([
    { $match: { deleted: { $ne: true } } },
    { $group: { _id: '$author', count: { $sum: 1 }, totalViews: { $sum: '$viewCount' } } },
    { $lookup: { from: 'users', localField: '_id', foreignField: '_id', as: 'author' } },
    { $unwind: '$author' },
    { $project: { _id: 0, username: '$author.username', count: 1, totalViews: 1 } },
  ]);
  console.log('[aggregate] 作者文章统计 =', JSON.stringify(stats, null, 2));
}

// ---------------------------------------------------------------------------
// 主流程
// ---------------------------------------------------------------------------
(async () => {
  await connect();
  await crudDemo();
  console.log('\n[完成] mongoose-crud.js 演示结束');
  await mongoose.disconnect(); // 关闭连接，进程退出
})().catch((err) => {
  console.error('[未捕获错误]', err);
  process.exit(1);
});
