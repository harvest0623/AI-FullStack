/**
 * ecosystem.config.js - PM2 生产环境配置
 * ------------------------------------------------------------
 * 作用: 让 PM2 以 cluster 模式拉起多个 Node 进程充分利用多核,
 *       内存超限自动重启, 并注入生产环境变量
 * 启动: pm2 start ecosystem.config.js --env production
 * 查看: pm2 status / pm2 logs / pm2 monit
 * 停止: pm2 stop day20-app  退出: pm2 delete day20-app
 * ------------------------------------------------------------
 */

module.exports = {
  apps: [
    {
      name: 'day20-app',                  // 进程名 (pm2 列表里显示的名字)
      script: './health-check.js',        // 入口文件

      // ---- cluster 模式 ----
      // fork: 单进程 (调试用); cluster: 多进程共享端口, 由内置负载均衡分发
      exec_mode: 'cluster',
      // 实例数: 'max' = CPU 核数; 数字 = 固定个数; 生产推荐 max 或核数
      instances: 'max',

      // ---- 自动重启策略 ----
      // 内存超 300MB 自动重启, 兜底内存泄漏 (治标, 真正要修泄漏)
      max_memory_restart: '300M',
      // 异常退出后重启间隔 (ms), 避免崩溃循环疯狂重启
      restart_delay: 3000,
      // 最大重启次数 (一段时间内), 超过则停止, 避免坏版本反复重启
      max_restarts: 10,
      min_uptime: '10s',                  // 启动后存活不足 10s 视为异常退出

      // ---- 优雅停机 (呼应 Day16) ----
      // PM2 发 SIGTERM 后等待应用主动退出的时间, 超时则 SIGKILL
      // 应用需监听 'SIGTERM' 关闭 http server 与数据库连接后再 exit
      kill_timeout: 5000,
      // SIGTERM 后若仍收到新请求, 用这个信号通知 "要关了"
      shutdown_with_message: false,

      // ---- 日志 (呼应 Day14) ----
      out_file: './logs/out.log',
      error_file: './logs/error.log',
      merge_logs: true,                   // 多实例日志合并到同一文件
      log_date_format: 'YYYY-MM-DD HH:mm:ss', // 每行日志加时间戳前缀
      // 合并日志后用 instance id 区分来源
      log_prefix: true,

      // ---- 环境变量 ----
      env: {                              // 默认环境 (不传 --env 时用)
        NODE_ENV: 'development',
        PORT: 3000
      },
      env_production: {                   // --env production 时覆盖
        NODE_ENV: 'production',
        PORT: 3000,
        LOG_LEVEL: 'info'
      }
    }
  ]
};
