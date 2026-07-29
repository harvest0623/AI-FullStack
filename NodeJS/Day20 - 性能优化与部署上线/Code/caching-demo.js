/**
 * caching-demo.js - 内存 LRU 缓存 + 查询缓存命中对比
 * ------------------------------------------------------------
 * 运行: node caching-demo.js
 *
 * 演示内容:
 *   1. 用 Map + maxSize 实现一个简易 LRU(最近最少使用) 缓存
 *      - Map 按插入顺序遍历, 访问时 delete+set 即可"提到最前"
 *      - 超容量时删掉 Map.first(最久未用)
 *   2. 模拟一个耗时数据库查询, 对比 "有缓存" vs "无缓存" 的耗时
 *
 * 适用边界:
 *   - 单机内存缓存, 进程重启即失效; 多实例需 Redis 等共享存储
 *   - 适合读多写少、可容忍短暂不一致的场景(配置、热门数据、模型元信息)
 * ------------------------------------------------------------
 */

'use strict';

const { performance } = require('perf_hooks');

// ============================================================
// 一、LRU 缓存实现
// ============================================================
class LRUCache {
  /**
   * @param {number} maxSize 最大条目数, 超出按 LRU 淘汰
   * @param {number} ttlMs   单条存活毫秒, 0 表示不过期
   */
  constructor(maxSize = 100, ttlMs = 0) {
    this.maxSize = maxSize;
    this.ttlMs = ttlMs;
    this.store = new Map(); // key -> { value, expireAt }
    this.hits = 0;
    this.misses = 0;
  }

  get(key) {
    const entry = this.store.get(key);
    if (!entry) {
      this.misses++;
      return undefined;
    }
    // TTL 过期则视为未命中并清理
    if (this.ttlMs > 0 && Date.now() > entry.expireAt) {
      this.store.delete(key);
      this.misses++;
      return undefined;
    }
    // LRU 关键: 重新插入, 让该 key 成为"最新使用"
    this.store.delete(key);
    this.store.set(key, entry);
    this.hits++;
    return entry.value;
  }

  set(key, value) {
    // 已存在则先删, 保证顺序更新
    if (this.store.has(key)) this.store.delete(key);
    this.store.set(key, {
      value,
      expireAt: this.ttlMs > 0 ? Date.now() + this.ttlMs : 0
    });
    // 超容淘汰: Map 的第一个元素就是最久未使用的
    if (this.store.size > this.maxSize) {
      const oldest = this.store.keys().next().value;
      this.store.delete(oldest);
    }
  }

  stats() {
    const total = this.hits + this.misses;
    return {
      size: this.store.size,
      hits: this.hits,
      misses: this.misses,
      hitRate: total === 0 ? 0 : (this.hits / total * 100).toFixed(1) + '%'
    };
  }
}

// ============================================================
// 二、模拟耗时数据库查询
// ============================================================
// 真实场景: 一次 DB 往返通常 5-50ms, 这里用同步忙等模拟, 便于不引入回调
function fakeDbQuery(userId) {
  const start = performance.now();
  // 忙等 20ms 模拟 IO 延迟 (生产中应是异步 await db.query)
  while (performance.now() - start < 20) { /* spin */ }
  return { id: userId, name: `用户${userId}`, email: `u${userId}@example.com`, fetchedAt: Date.now() };
}

// 带缓存的查询: 命中则直接返回, 未命中则查库并回填
function queryWithCache(userId, cache) {
  const cached = cache.get(userId);
  if (cached) return { ...cached, fromCache: true };
  const fresh = fakeDbQuery(userId);
  cache.set(userId, fresh);
  return { ...fresh, fromCache: false };
}

// ============================================================
// 三、对比: 有缓存 vs 无缓存
// ============================================================
function runBenchmark() {
  const USER_IDS = Array.from({ length: 50 }, (_, i) => i + 1);
  // 模拟"热点访问": 同一批用户被重复查询 5 轮 (读多写少典型场景)
  const ROUNDS = 5;

  console.log('=== 场景 1: 无缓存, 每次都查库 ===');
  let noCacheTotal = 0;
  for (let r = 0; r < ROUNDS; r++) {
    const t0 = performance.now();
    for (const id of USER_IDS) fakeDbQuery(id);
    const dt = performance.now() - t0;
    noCacheTotal += dt;
  }
  console.log(`  ${ROUNDS} 轮 × ${USER_IDS.length} 用户 = ${ROUNDS * USER_IDS.length} 次查询`);
  console.log(`  总耗时: ${noCacheTotal.toFixed(1)}ms, 平均 ${(noCacheTotal / (ROUNDS * USER_IDS.length)).toFixed(2)}ms/次\n`);

  console.log('=== 场景 2: LRU 缓存, 首次查库后续命中 ===');
  const cache = new LRUCache(200, 60_000);
  let cacheTotal = 0;
  for (let r = 0; r < ROUNDS; r++) {
    const t0 = performance.now();
    for (const id of USER_IDS) queryWithCache(id, cache);
    const dt = performance.now() - t0;
    cacheTotal += dt;
    console.log(`  第 ${r + 1} 轮耗时: ${dt.toFixed(1)}ms${r === 0 ? ' (首轮全 miss)' : ' (全命中)'}`);
  }
  console.log(`  总耗时: ${cacheTotal.toFixed(1)}ms, 平均 ${(cacheTotal / (ROUNDS * USER_IDS.length)).toFixed(3)}ms/次`);

  console.log('\n=== 缓存统计 ===');
  console.log(' ', cache.stats());

  // ============================================================
  // 四、LRU 淘汰验证
  // ============================================================
  console.log('\n=== LRU 淘汰验证 ===');
  const small = new LRUCache(3);
  small.set('a', 1);
  small.set('b', 2);
  small.set('c', 3);
  small.get('a');           // 访问 a, a 变最新, 顺序: b c a
  small.set('d', 4);        // 超容, 淘汰最旧的 b
  console.log(`  容量3, 写入a/b/c, 访问a, 再写d → 期望保留 a c d`);
  console.log(`  a=${small.get('a')}, b=${small.get('b')}, c=${small.get('c')}, d=${small.get('d')}`);

  console.log('\n----------------------------------------');
  console.log('结论:');
  console.log('  · 读多写少场景下, 缓存能把平均耗时从 ~20ms 降到亚毫秒级');
  console.log('  · LRU 保证容量受限, 自动淘汰冷数据, 防止内存无限增长');
  console.log('  · 多实例部署需把缓存提到 Redis, 否则各实例缓存不一致且重复');
}

runBenchmark();
