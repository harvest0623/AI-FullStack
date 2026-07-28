// cluster-http.js - cluster 模块多核 HTTP 服务器
// 运行:
//   node cluster-http.js
//
// 测试访问:
//   浏览器或 curl http://localhost:3000
//   多次访问会看到 pid 在多个值之间轮换(RR 调度把请求分给不同 worker)
//
// 压测(任选其一):
//   # 1. 用自带的 ab(Apache Bench)
//   ab -n 10000 -c 100 http://localhost:3000/
//   # -n 总请求数, -c 并发数
//   # 关注 Requests per second 和 Failed requests
//
//   # 2. 用 wrk(更现代, 推荐)
//   wrk -t8 -c100 -d10s http://localhost:3000/
//   # -t 线程数(建议 <= CPU 核数), -c 连接数, -d 持续时间
//
//   # 3. Windows 无 ab/wrk 可用 PowerShell 并发请求
//   1..1000 | ForEach-Object -Parallel { (Invoke-WebRequest -UseBasicParsing http://localhost:3000).Content } -ThrottleLimit 50
//
// 验证多核利用:
//   压测时另开终端看 CPU:
//     Linux/Mac: top -p $(pgrep -d, node)   # 会看到多个 node 进程各占一个核
//     Windows:   任务管理器 -> 性能 -> CPU, 会看到多个核都跑满
//   对比: 把下面 cluster.isPrimary 直接改成 false(走单进程分支)再压测,
//        只有一个核会跑满, QPS 明显更低。

const cluster = require('cluster');
const http = require('http');
const os = require('os');

const PORT = 3000;

// ---------------------------------------------------------------
// 调度策略: 必须在 fork 之前设置
//   SCHED_RR  : round-robin, master 轮流分发连接, 分配均匀(非 Windows 默认)
//   SCHED_NONE: 共享套接字, 由 OS 内核抢占, 可能有惊群效应(Windows 默认)
// 这里显式设 RR, 保证跨平台行为一致
// ---------------------------------------------------------------
cluster.schedulingPolicy = cluster.SCHED_RR;

// ---------------------------------------------------------------
// 主进程: 只负责 fork worker、监听崩溃重启, 不处理业务请求
// ---------------------------------------------------------------
if (cluster.isPrimary) {
  // isPrimary 是 Node 16+ 推荐写法, 旧代码里的 isMaster 是它的别名
  const numCPUs = os.cpus().length;
  console.log(`[master] 主进程启动 pid=${process.pid}`);
  console.log(`[master] 检测到 ${numCPUs} 个 CPU 核心, 将 fork ${numCPUs} 个 worker`);
  console.log(`[master] 服务监听 http://localhost:${PORT}`);
  console.log('------------------------------------------------');

  // fork 出与 CPU 核数相同的 worker
  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }

  // ---------------------------------------------------------------
  // 监听 worker 生命周期事件
  // 触发顺序: fork -> online -> listening -> (运行) -> exit
  // ---------------------------------------------------------------
  cluster.on('fork', (worker) => {
    console.log(`[master] 正在 fork worker id=${worker.id}`);
  });

  cluster.on('online', (worker) => {
    // worker 启动并连上 IPC 通道后触发
    console.log(`[master] worker ${worker.id} 上线, pid=${worker.process.pid}`);
  });

  cluster.on('listening', (worker, address) => {
    // worker 调用 server.listen 成功后触发, 此时 worker 真正可服务
    console.log(`[master] worker ${worker.id} 监听端口 ${address.port} 成功`);
  });

  // ---------------------------------------------------------------
  // 核心: worker 崩溃后自动重启
  // 没有 this, 服务少一个进程, 处理能力下降
  // ---------------------------------------------------------------
  cluster.on('exit', (worker, code, signal) => {
    console.error(
      `[master] worker ${worker.id} (pid=${worker.process.pid}) 退出, code=${code} signal=${signal || '(无)'}`
    );

    // 注意: 这里无条件 fork 补齐。
    // 即使 worker 主动 process.exit(0) 也算"正常退出", 但服务少了一个进程仍需补齐。
    // 若在做"缩容"(主动减少 worker 数), 则需用标志位跳过 fork。
    console.log(`[master] 重启一个新 worker 补位...`);
    cluster.fork();
  });

  // 主进程自身也可被 SIGINT/SIGTERM 优雅关闭(见 graceful-shutdown.js)
  process.on('SIGINT', () => {
    console.log('\n[master] 收到 SIGINT, 关闭所有 worker');
    // disconnect 所有 worker 后主进程自然退出
    for (const worker of Object.values(cluster.workers)) {
      worker.disconnect();
    }
    setTimeout(() => process.exit(0), 1000).unref();
  });

} else {
  // ---------------------------------------------------------------
  // worker 进程: 跑 HTTP 服务, 共享主进程绑定的端口
  // 同一份脚本走到这里: cluster.isPrimary 为 false, cluster.isWorker 为 true
  // ---------------------------------------------------------------
  const workerId = cluster.worker.id; // cluster 内部逻辑编号, 重启会变
  const pid = process.pid;            // OS 进程号, ps 能看到

  const server = http.createServer((req, res) => {
    // 模拟一点业务耗时(I/O 密集型, 不阻塞事件循环)
    setTimeout(() => {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        message: 'Hello from cluster worker',
        workerId,                    // 哪个 worker 处理的
        pid,                         // 该 worker 的进程号
        uptimeSec: process.uptime().toFixed(2) // 该 worker 已运行秒数
      }));
    }, 10);
  });

  // 关键: worker 调 listen(3000) 并不会真的在 worker 内绑定端口,
  // 而是通过 IPC 告诉 master "我要监听", 由 master 绑定并分发连接。
  // 这就是多 worker 共享同一端口的底层机制。
  server.listen(PORT);

  console.log(`[worker ${workerId}] 启动, pid=${pid}, 监听 :${PORT}`);

  // ---------------------------------------------------------------
  // 演示: 模拟随机崩溃(默认关闭, 取消注释可测试自动重启)
  // 开启后每隔一段有概率抛未捕获异常, master 会自动拉起新 worker
  // ---------------------------------------------------------------
  // setInterval(() => {
  //   if (Math.random() < 0.05) {
  //     throw new Error(`[worker ${workerId}] 模拟随机崩溃`);
  //   }
  // }, 2000).unref();

  // ---------------------------------------------------------------
  // worker 也可监听来自 master 的 IPC 消息(见 worker-ipc-demo.js)
  // ---------------------------------------------------------------
  process.on('message', (msg) => {
    if (msg === 'shutdown') {
      // master 请求优雅关闭: 停止接受新连接, 处理完在途请求后退出
      console.log(`[worker ${workerId}] 收到 shutdown 指令, 优雅关闭`);
      server.close(() => {
        console.log(`[worker ${workerId}] 在途请求处理完毕, 退出`);
        process.exit(0);
      });
    }
  });
}

// ---------------------------------------------------------------
// 关键结论
// ---------------------------------------------------------------
/*
  1. cluster = 1 个 master + N 个 worker, master 不干活只调度
  2. 所有 worker 共享同一端口, 底层靠 IPC + 句柄分发实现
  3. isPrimary / isWorker 区分角色, 同一份脚本分流到不同分支
  4. 必须监听 worker 的 exit 事件并 fork 补位, 否则崩一个少一个
  5. schedulingPolicy = SCHED_RR 是推荐策略, 分配均匀
  6. 压测对比: 单进程 vs cluster, QPS 接近 N 倍(N = CPU 核数)
  7. 生产环境通常不手写 cluster, 直接用 PM2(底层就是 cluster + 运维工具链)
*/
