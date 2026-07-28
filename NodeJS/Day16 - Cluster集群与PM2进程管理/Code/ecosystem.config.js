// ecosystem.config.js - PM2 配置文件
// 用法:
//   # 启动(用默认 env)
//   pm2 start ecosystem.config.js
//
//   # 启动并用 env_production(合并覆盖 env, 同名键以 env_production 为准)
//   pm2 start ecosystem.config.js --env production
//
//   # 零停机重载(发布新代码, 仅 cluster 模式有效)
//   pm2 reload ecosystem.config.js --env production
//
//   # 完全重启(有短暂空窗, 配置大改时用)
//   pm2 restart ecosystem.config.js --env production
//
//   # 停止 / 删除
//   pm2 stop ecosystem.config.js
//   pm2 delete ecosystem.config.js
//
//   # 查看状态 / 监控 / 日志
//   pm2 status
//   pm2 monit
//   pm2 logs ai-api --lines 100
//
//   # 保存进程列表 + 开机自启(裸机部署)
//   pm2 save
//   pm2 startup

/**
 * PM2 ecosystem 配置文件
 *
 * 这是一个 CommonJS 模块, 导出 { apps: [...] } 数组。
 * 每个 app 对应一个被 PM2 管理的应用, 可以一次管理多个应用。
 */
module.exports = {
  apps: [
    // ===================================================
    // 应用 1: AI 接口服务(主服务, cluster 模式吃满多核)
    // ===================================================
    {
      name: 'ai-api',                // 应用名: pm2 status 里显示的标识, 后续 stop/reload 用它
      script: './app.js',            // 入口脚本路径(相对 cwd)。实际项目里指向你的 Express/Koa 入口
      cwd: __dirname,                // 工作目录, 脚本与日志路径以此为基准

      // ---- 多核扩展 ----
      instances: 'max',              // worker 数量。'max' = CPU 核数; 也可写数字如 4
                                      // cluster 模式建议 'max' 或核数, fork 模式写 1
      exec_mode: 'cluster',          // 'cluster': 多进程共享端口(底层 cluster 模块), 支持 reload 零停机
                                      // 'fork':    单进程, 类似直接 node 启动, 不支持 reload

      // ---- 自动重启策略 ----
      max_memory_restart: '500M',    // 单 worker 内存超 500M 自动重启, 防内存泄漏拖垮机器
                                      // 格式: '500M' / '1G' / '200K'
      max_restarts: 10,              // 单位时间(min_uptime 窗口)内最大重启次数, 超过认为"反复崩溃"
      min_uptime: '10s',             // worker 启动后存活少于 10s 视为"异常退出", 计入 max_restarts
      exp_backoff_restart_delay: 200,// 指数退避重启延迟(ms), 防雪崩: 每次重启失败延迟翻倍

      // ---- 优雅退出 ----
      kill_timeout: 3000,            // 发 SIGTERM 后等 3s, 超时则 SIGKILL 强杀
                                      // 你的 server.close 超时要小于这个值
      listen_timeout: 5000,          // fork 后 5s 内未 listening 视为启动失败

      // ---- 日志 ----
      out_file: './logs/ai-api-out.log',   // stdout 输出文件(console.log)
      error_file: './logs/ai-api-error.log', // stderr 输出文件(console.error)
      merge_logs: true,              // cluster 模式下多个 worker 的日志合并到同一文件(不加 __1 __2 后缀)
      log_date_format: 'YYYY-MM-DD HH:mm:ss', // 日志加时间戳前缀, 便于排查

      // ---- 环境变量 ----
      // env 是基础环境, 所有模式都生效
      // env_<name> 用 --env <name> 激活, 会"合并覆盖"到 env 之上(同名键以 env_<name> 为准)
      env: {                         // 默认环境(不加 --env 时用, 通常对应开发)
        NODE_ENV: 'development',
        PORT: 3000,
        LOG_LEVEL: 'debug'
      },
      env_production: {              // --env production 时用(合并覆盖 env)
        NODE_ENV: 'production',
        PORT: 8080,
        LOG_LEVEL: 'info'
      },

      // ---- 其他 ----
      autorestart: true,             // worker 崩溃自动重启(默认 true)
      watch: false,                  // 文件变化自动重启(开发用, 生产务必 false)
      instance_var: 'NODE_APP_INSTANCE', // worker 实例编号注入到 process.env 的变量名
      // 命令行追加参数(传给脚本 process.argv)
      args: '--serve'
    },

    // ===================================================
    // 应用 2: 后台任务 worker(消费者, fork 模式单进程)
    // 演示 ecosystem 可同时管理多个不同类型的应用
    // ===================================================
    {
      name: 'ai-worker',             // 任务 worker 名
      script: './worker.js',         // 入口(消费消息队列、跑定时任务)
      instances: 1,                  // 单实例: 消费者通常不需要多核(避免重复消费)
      exec_mode: 'fork',             // fork 模式: 不监听端口, 不需要 cluster
      max_memory_restart: '300M',
      env: {
        NODE_ENV: 'development',
        QUEUE_NAME: 'ai-tasks'
      },
      env_production: {
        NODE_ENV: 'production',
        QUEUE_NAME: 'ai-tasks-prod'
      },
      out_file: './logs/ai-worker-out.log',
      error_file: './logs/ai-worker-error.log',
      merge_logs: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    }
  ]
};

// ---------------------------------------------------------------
// 关键字段速查表
// ---------------------------------------------------------------
/*
  ┌──────────────────────┬──────────────────────────────────────────────────┐
  │ 字段                  │ 说明                                              │
  ├──────────────────────┼──────────────────────────────────────────────────┤
  │ name                 │ 应用名(pm2 status 标识, stop/reload 用它)         │
  │ script               │ 入口脚本路径                                      │
  │ cwd                  │ 工作目录                                          │
  │ instances            │ worker 数: 'max'/数字, cluster 用 max, fork 用 1  │
  │ exec_mode            │ 'cluster'(多核+reload) / 'fork'(单进程)          │
  │ max_memory_restart   │ 内存阈值重启, 防泄漏                              │
  │ max_restarts         │ 短时间最大重启次数, 防雪崩                        │
  │ min_uptime           │ 启动存活少于该值视为异常退出                      │
  │ exp_backoff_restart_delay │ 指数退避重启延迟                            │
  │ kill_timeout         │ SIGTERM 后等多久强杀(ms)                         │
  │ listen_timeout       │ fork 后多久未 listening 视为失败                  │
  │ out_file/error_file  │ 日志文件路径                                      │
  │ merge_logs           │ 多 worker 日志合并                                │
  │ log_date_format      │ 日志时间戳格式                                    │
  │ env                  │ 基础环境变量                                      │
  │ env_<name>           │ --env <name> 激活的环境(覆盖 env)                 │
  │ autorestart          │ 崩溃自动重启(默认 true)                          │
  │ watch                │ 文件变化重启(开发用, 生产 false)                 │
  │ args                 │ 传给脚本的命令行参数                              │
  └──────────────────────┴──────────────────────────────────────────────────┘

  环境变量合并规则:
    pm2 start ecosystem.config.js                  → 只用 env
    pm2 start ecosystem.config.js --env production → env + env_production(后者覆盖同名键)

    例: env 有 PORT:3000, env_production 有 PORT:8080
        --env production 时 PORT=8080(被覆盖), NODE_ENV=production(新增)
*/
