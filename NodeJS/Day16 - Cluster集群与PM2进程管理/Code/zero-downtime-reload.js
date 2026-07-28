// zero-downtime-reload.js - 零停机重启演示(逐个重启 worker)
// 运行:
//   node zero-downtime-reload.js
//
// 测试零停机重启:
//   # 终端 1: 启动服务
//   node zero-downtime-reload.js
//
//   # 终端 2: 持续发请求, 观察响应是否中断(不应中断)
//   #   Linux/Mac:
//   while true; do curl -s http://localhost:3000/; echo; sleep 0.2; done
//   #   Windows PowerShell:
//   while ($true) { (Invoke-WebRequest -UseBasicParsing http://localhost:3000/).Content; Start-Sleep -Milliseconds 200 }
//
//   # 终端 3: 触发零停机重启(向 master 发 SIGUSR2 信号)
//   #   Linux/Mac:  kill -USR2 <master_pid>
//   #   Windows:    本 demo 额外提供了 HTTP 触发端点:
//   curl http://localhost:3000/__reload
//   #   (Windows 不支持 USR2 信号, 故用 HTTP 端点触发)
//
//   # 观察终端 2: 整个 reload 过程请求不中断(可能偶有延迟但不会连接拒绝),
//   #             worker pid 逐个被替换为新值, 但任意时刻都有 worker 在服务。
//
// 注意:
//   本文件演示手写零停机重启原理。生产环境直接用 PM2:
//     pm2 reload ecosystem.config.js
//   PM2 的 reload 已封装此逻辑, 并额外处理了超时强杀、环境变量更新等边界情况。

const cluster = require('cluster');
const http = require('http');
const os = require('os');

const PORT = 3000;
cluster.schedulingPolicy = cluster.SCHED_RR;

// ---------------------------------------------------------------
// 主进程
// ---------------------------------------------------------------
if (cluster.isPrimary) {
  const numCPUs = os.cpus().length;
  console.log(`[master] 启动 pid=${process.pid}, fork ${numCPUs} 个 worker`);

  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }

  cluster.on('online', (worker) => {
    console.log(`[master] worker ${worker.id} 上线 pid=${worker.process.pid}`);
  });

  // 崩溃自动重启(与 cluster-http.js 一致)
  cluster.on('exit', (worker, code, signal) => {
    console.log(`[master] worker ${worker.id} 退出 code=${code} signal=${signal}`);
    if (!isReloading) {
      // 非主动 reload 期间的崩溃, 才自动补位
      console.log('[master] 非计划退出, 自动重启补位');
      cluster.fork();
    }
  });

  // ---------------------------------------------------------------
  // 零停机重启核心逻辑: 逐个重启 worker
  //   思路: 先 fork 新 worker, 等它 listening 能服务后, 再 disconnect 旧 worker
  //         这样任意时刻都有足够数量的 worker 在服务, 外部感受不到停机
  //   这正是 PM2 reload 的底层思路
  // ---------------------------------------------------------------
  let isReloading = false;

  function zeroDowntimeReload() {
    if (isReloading) {
      console.log('[master] 已有 reload 进行中, 跳过');
      return;
    }
    isReloading = true;

    // 取当前所有存活的 worker(快照)
    const oldWorkers = Object.values(cluster.workers).filter((w) => !w.isDead());
    console.log(`\n[master] === 开始零停机重启, 共 ${oldWorkers.length} 个 worker 需替换 ===`);

    let replaced = 0;

    function replaceNext() {
      if (replaced >= oldWorkers.length) {
        // 所有旧 worker 都已替换完毕
        isReloading = false;
        console.log('[master] === 零停机重启完成, 所有 worker 已更新 ===\n');
        return;
      }

      const oldWorker = oldWorkers[replaced];
      console.log(`[master] 替换 worker ${oldWorker.id} (pid=${oldWorker.process.pid})`);

      // 步骤 1: 先 fork 新 worker(加载最新代码)
      const newWorker = cluster.fork();

      // 步骤 2: 等新 worker listening(就绪可服务)后, 再停旧 worker
      newWorker.on('listening', () => {
        console.log(`[master] 新 worker ${newWorker.id} (pid=${newWorker.process.pid}) 已就绪, 开始停旧 worker ${oldWorker.id}`);

        // 旧 worker 退出后, 继续替换下一个
        oldWorker.on('exit', () => {
          console.log(`[master] 旧 worker ${oldWorker.id} 已退出`);
          replaced++;
          replaceNext();
        });

        // disconnect: 优雅关闭旧 worker
        //   关 IPC + 停止接受新连接, 但已建立的在途请求会处理完
        oldWorker.disconnect();

        // 超时保护: 旧 worker 5 秒内未退出则强杀(防在途请求卡死)
        setTimeout(() => {
          if (!oldWorker.isDead()) {
            console.warn(`[master] 旧 worker ${oldWorker.id} 超时未退出, 强杀`);
            oldWorker.kill('SIGKILL');
          }
        }, 5000).unref();
      });

      // 新 worker 启动失败的处理
      newWorker.on('exit', (code) => {
        if (code !== 0) {
          console.error(`[master] 新 worker ${newWorker.id} 启动失败 code=${code}, 中止 reload`);
          isReloading = false;
        }
      });
    }

    replaceNext();
  }

  // ---------------------------------------------------------------
  // 触发方式 1: HTTP 端点(跨平台, Windows 友好)
  //   访问 http://localhost:3000/__reload 触发零停机重启
  // 注意: 生产环境务必加鉴权, 这里仅演示
  // ---------------------------------------------------------------
  http.createServer((req, res) => {
    if (req.url === '/__reload') {
      res.writeHead(200, { 'Content-Type': 'text/plain' });
      res.end('reload triggered, check server logs\n');
      zeroDowntimeReload();
      return;
    }
    // master 不处理业务请求, 这个 http 服务仅用于接收 reload 指令
    res.writeHead(404);
    res.end('not found (master control port)\n');
  }).listen(PORT + 1, () => {
    console.log(`[master] reload 控制端点 http://localhost:${PORT + 1}/__reload`);
    console.log('[master] 也可用 kill -USR2 <pid> 触发(Linux/Mac)\n');
  });

  // ---------------------------------------------------------------
  // 触发方式 2: SIGUSR2 信号(Linux/Mac)
  //   kill -USR2 <master_pid>
  //   Windows 不支持 USR2, 故额外提供 HTTP 端点
  // ---------------------------------------------------------------
  process.on('SIGUSR2', () => {
    console.log('[master] 收到 SIGUSR2, 触发零停机重启');
    zeroDowntimeReload();
  });

} else {
  // ---------------------------------------------------------------
  // worker 进程: 跑业务 HTTP 服务
  // ---------------------------------------------------------------
  const workerId = cluster.worker.id;
  const pid = process.pid;
  const startTime = Date.now();

  http.createServer((req, res) => {
    // 模拟一点业务耗时
    setTimeout(() => {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        workerId,
        pid,
        uptimeSec: ((Date.now() - startTime) / 1000).toFixed(1)
      }));
    }, 20);
  }).listen(PORT);

  console.log(`[worker ${workerId}] 启动 pid=${pid}, 监听 :${PORT}`);

  // 配合 master 的 disconnect 优雅退出
  process.on('message', (msg) => {
    if (msg === 'shutdown') {
      console.log(`[worker ${workerId}] 收到 shutdown, 优雅关闭`);
      process.exit(0);
    }
  });
}

// ---------------------------------------------------------------
// 关键结论
// ---------------------------------------------------------------
/*
  零停机重启原理:
    1. 逐个替换 worker, 而非一次性全停全启
    2. 先 fork 新 worker, 等它 listening(就绪) 后再 disconnect 旧 worker
    3. 任意时刻都有足够数量的 worker 在服务, 外部感受不到停机
    4. 旧 worker 用 disconnect 优雅关闭(处理完在途请求), 超时才 kill 强杀

  与 PM2 reload 的关系:
    - PM2 的 `pm2 reload` 就是这个逻辑的封装版
    - PM2 额外处理了: kill_timeout 配置、环境变量更新(--update-env)、
      reload 失败回滚、多应用批量 reload
    - 生产环境直接用 pm2 reload, 不需要手写

  reload vs restart:
    - restart: 杀掉所有 worker 再 fork, 有短暂空窗(连接拒绝)
    - reload:  逐个替换, 新旧并存过渡, 零停机(仅 cluster 模式有效)

  注意事项:
    - reload 期间偶有请求仍打到旧 worker(还没被 disconnect), 返回旧版本
    - 这是正常的"最终一致", 不算停机, 但客户端可能短暂看到版本混杂
    - 若业务对版本敏感(如数据库 schema 变更), 需额外做版本协商
*/
