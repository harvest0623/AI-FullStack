/**
 * Day04 - 异步编程（回调与事件循环）
 * 文件：callback-hell.js
 * 主题：回调地狱（Callback Hell）演示
 *
 * 场景：模拟一个"用户下单后查物流"的串行流程
 *   1. 第 1 层：读取用户配置（200ms）—— 用 setTimeout 模拟
 *   2. 第 2 层：根据用户配置读取订单（200ms）—— 用 setTimeout 模拟
 *   3. 第 3 层：根据订单读取物流信息（200ms）—— 用 fs 模拟文件操作
 *
 * 三层嵌套形成"金字塔"，这就是回调地狱。
 *
 * 重点注释：在每层嵌套处标注问题所在。
 */

'use strict';

const fs = require('fs');
const path = require('path');

// 模拟数据
const mockConfig = { userId: 1, region: 'cn-beijing' };
const mockOrder = { orderId: 'ORD-2024-001', items: ['MacBook', 'iPhone'] };
const mockLogistics = {
  orderId: 'ORD-2024-001',
  status: '运输中',
  location: '北京转运中心',
};

/**
 * 第 1 层：读取用户配置（模拟异步 I/O）
 */
function loadConfig(userId, callback) {
  console.log(`[第1层开始] 读取用户 ${userId} 的配置...`);
  setTimeout(() => {
    if (userId !== mockConfig.userId) {
      return callback(new Error('用户不存在'));
    }
    callback(null, mockConfig);
  }, 200);
}

/**
 * 第 2 层：读取订单（模拟异步 I/O）
 */
function loadOrders(config, callback) {
  console.log(`[第2层开始] 根据配置读取订单，region=${config.region}...`);
  setTimeout(() => {
    callback(null, mockOrder);
  }, 200);
}

/**
 * 第 3 层：读取物流信息（模拟真实文件 I/O）
 * 这里用 fs.writeFile + fs.readFile 模拟一次"持久化后再读"的过程
 */
function loadLogistics(order, callback) {
  console.log(`[第3层开始] 读取订单 ${order.orderId} 的物流...`);

  const tmpFile = path.join(__dirname, '.logistics-tmp.json');

  // 先把订单信息写到临时文件，再读回来——模拟"先存再查"
  fs.writeFile(tmpFile, JSON.stringify(mockLogistics), (writeErr) => {
    if (writeErr) {
      // ⚠️ 问题点 A：错误处理嵌套在多层里，每一层都要重复 if (err) return ...
      return callback(writeErr);
    }

    fs.readFile(tmpFile, 'utf8', (readErr, data) => {
      // ⚠️ 问题点 B：到这里已经嵌套了 3 层，代码缩进难以阅读
      if (readErr) {
        return callback(readErr);
      }

      try {
        // ⚠️ 问题点 C：JSON.parse 可能抛错，必须用 try/catch
        // 而且这个 try/catch 捕获的是同步错误，回调里的 throw 是无法被外层捕获的
        const logistics = JSON.parse(data);
        callback(null, logistics);
      } catch (parseErr) {
        callback(parseErr);
      } finally {
        // 清理临时文件（这里同步删除，实际项目应异步）
        try {
          fs.unlinkSync(tmpFile);
        } catch (_) {
          /* 忽略清理错误 */
        }
      }
    });
  });
}

/**
 * 主流程：三层嵌套的"回调地狱"
 */
function main() {
  console.log('=== 回调地狱演示 ===\n');
  console.log('开始执行串行任务：读配置 → 读订单 → 读物流\n');

  // 第 1 层
  loadConfig(1, (err, config) => {
    // ⚠️ 问题点 1：错误处理分散，每一层都要写 if (err) return ...
    if (err) {
      console.error('❌ 第1层失败:', err.message);
      return;
    }
    console.log('✅ 第1层完成:', config, '\n');

    // 第 2 层：嵌套在第 1 层的回调里
    loadOrders(config, (err, order) => {
      // ⚠️ 问题点 2：缩进开始向右"金字塔"膨胀
      if (err) {
        console.error('❌ 第2层失败:', err.message);
        return;
      }
      console.log('✅ 第2层完成:', order, '\n');

      // 第 3 层：再嵌套一层
      loadLogistics(order, (err, logistics) => {
        // ⚠️ 问题点 3：到第 3 层时缩进已经 6 个空格，业务逻辑被嵌套结构淹没
        if (err) {
          console.error('❌ 第3层失败:', err.message);
          return;
        }
        console.log('✅ 第3层完成:', logistics, '\n');

        // ⚠️ 问题点 4：如果想在这里 return 给 main 的调用方，做不到
        // 因为整个流程被埋在 3 层回调里，没有"出口"
        console.log('🎉 全流程完成：用户已查到物流信息');

        // ⚠️ 问题点 5：如果后续还要做 4、5、6 步骤，会继续嵌套
        // 这就是为什么需要 Promise / async-await 的根本原因
      });
    });
  });

  console.log('（同步代码已结束，等待异步回调...）\n');
}

main();

/**
 * 回调地狱的核心问题总结（在代码注释中明确指出）：
 *
 * 1. 【可读性】嵌套层级深，代码向右"金字塔"膨胀，难以快速理解控制流
 * 2. 【错误处理】每一层都要重复 if (err) return ...，容易遗漏导致错误被吞
 * 3. 【无法 return/throw】异步回调里的 return 不会回到调用方，throw 会变成 uncaughtException
 * 4. 【难以复用】每一步逻辑被绑死在嵌套里，无法单独抽取和测试
 * 5. 【变量作用域混乱】内层可以访问外层变量，容易出现意外的闭包陷阱
 * 6. 【try/catch 失效】同步的 try/catch 无法捕获异步回调里的错误，必须用回调传递
 *
 * 解决方案（Day05 详解）：
 *   - Promise：用 .then() 链式调用替代嵌套
 *   - async/await：用同步写法写异步代码，try/catch 重新可用
 *   - 控制流库：async.js 等（已逐渐被 Promise 取代）
 *
 * 运行：node callback-hell.js
 * 预期总耗时约 600ms（3 层 × 200ms）
 */
