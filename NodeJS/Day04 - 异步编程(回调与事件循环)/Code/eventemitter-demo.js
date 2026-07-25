/**
 * Day04 - 异步编程（回调与事件循环）
 * 文件：eventemitter-demo.js
 * 主题：自定义事件类继承 EventEmitter
 *
 * 演示：
 *   1. 自定义类继承 events.EventEmitter
 *   2. on / once / emit / off 的基本用法
 *   3. setMaxListeners 调整监听器上限（默认 10）
 *   4. error 事件约定（未监听会让进程崩溃）
 *
 * 场景：模拟一个"任务处理器"，对外抛出 start / progress / done / error 事件
 */

'use strict';

const { EventEmitter } = require('events');

/**
 * 自定义任务处理器，继承 EventEmitter
 */
class TaskRunner extends EventEmitter {
  constructor(taskName) {
    super(); // 必须调用 super()，否则 this 不可用
    this.taskName = taskName;
    this.isRunning = false;

    // 调整监听器上限：默认 10，这里设为 20
    // 假设多个模块（日志、监控、UI）都会监听 progress 事件
    this.setMaxListeners(20);
  }

  /**
   * 启动任务，模拟进度推进
   */
  start() {
    if (this.isRunning) {
      // ⚠️ error 事件约定：emit('error', err) 若无监听器，进程会崩溃
      // 这里我们故意触发一个 error 事件演示约定（main 里已注册 error 监听器）
      this.emit('error', new Error(`任务 ${this.taskName} 已在运行`));
      return;
    }

    this.isRunning = true;
    let progress = 0;

    // 触发 start 事件
    this.emit('start', { taskName: this.taskName, startTime: Date.now() });

    // 用 setInterval 模拟任务进度
    const timer = setInterval(() => {
      progress += 20;

      // 10% 概率随机失败
      if (Math.random() < 0.1) {
        clearInterval(timer);
        this.isRunning = false;
        this.emit('error', new Error(`任务 ${this.taskName} 在 ${progress}% 时随机失败`));
        return;
      }

      // 触发 progress 事件，携带进度数据
      this.emit('progress', { taskName: this.taskName, progress });

      if (progress >= 100) {
        clearInterval(timer);
        this.isRunning = false;
        // 触发完成事件
        this.emit('done', { taskName: this.taskName, finishTime: Date.now() });
      }
    }, 200);
  }
}

/**
 * 主函数：演示各种监听器用法
 */
function main() {
  console.log('=== EventEmitter 演示 ===\n');

  const runner = new TaskRunner('数据迁移');

  // 1. on：注册持续监听器（每次 emit 都会触发）
  runner.on('start', (info) => {
    console.log(`▶️  [start] 任务开始：${info.taskName}，开始时间戳：${info.startTime}`);
  });

  runner.on('progress', (info) => {
    console.log(`⏳ [progress] ${info.taskName} 进度：${info.progress}%`);
  });

  // 2. once：只触发一次的监听器
  runner.once('done', (info) => {
    console.log(`✅ [done] 任务完成：${info.taskName}，完成时间戳：${info.finishTime}`);
    console.log('   （once 监听器只触发一次，之后自动移除）');
  });

  // 3. error 事件：必须监听，否则 emit('error') 会让进程崩溃
  runner.on('error', (err) => {
    console.error(`❌ [error] 捕获错误：${err.message}`);
  });

  // 4. off / removeListener：移除指定监听器（需保留函数引用）
  const logProgress = (info) => {
    console.log(`   📝 [额外日志] ${info.taskName} 当前进度：${info.progress}%`);
  };
  runner.on('progress', logProgress);

  // 演示：3 秒后移除额外日志监听器
  setTimeout(() => {
    runner.off('progress', logProgress);
    console.log('\n   ⛔ [off] 已移除"额外日志"监听器\n');
  }, 700);

  // 5. 演示监听器上限警告（默认 10，我们已设为 20）
  console.log('--- 监听器上限演示 ---');
  console.log(`当前 progress 事件的监听器数量：${runner.listenerCount('progress')}`);
  console.log(`当前最大监听器上限：${runner.getMaxListeners()}`);

  // 故意注册多个监听器，验证 setMaxListeners 的效果
  for (let i = 0; i < 15; i++) {
    runner.on('progress', () => {}); // 空函数，仅用于计数
  }
  console.log(`再注册 15 个后，progress 监听器数量：${runner.listenerCount('progress')}`);
  console.log('（因为我们已 setMaxListeners(20)，所以不会触发警告）\n');

  // 6. listeners：返回监听器数组
  console.log(`progress 事件的监听器数组长度：${runner.listeners('progress').length}\n`);

  // 启动任务
  console.log('--- 启动任务 ---\n');
  runner.start();

  // 演示：重复启动触发 error 事件
  setTimeout(() => {
    console.log('\n--- 演示重复启动触发 error 事件 ---');
    runner.start(); // 此时任务可能还在运行，会触发 error
  }, 100);
}

main();

/**
 * 运行：node eventemitter-demo.js
 *
 * 关键点回顾：
 *   - on：注册持续监听器
 *   - once：注册一次性监听器（自动移除）
 *   - emit：同步触发事件，依次调用所有监听器
 *   - off / removeListener：移除监听器（必须传同一个函数引用）
 *   - setMaxListeners：调整上限（默认 10），超过会警告但不报错
 *   - error 事件：未监听时 emit('error') 会让进程崩溃，必须注册 error 处理器
 */
