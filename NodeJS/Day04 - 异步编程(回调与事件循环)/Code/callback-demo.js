/**
 * Day04 - 异步编程（回调与事件循环）
 * 文件：callback-demo.js
 * 主题：错误优先回调（error-first callback）示例
 *
 * 错误优先约定（Node-style callback）：
 *   callback 的第一个参数永远是错误对象（成功时为 null），后续参数才是真实数据
 *   形如：function (err, data) { ... }
 *
 * 本示例：模拟从"数据库"读取用户信息，演示：
 *   1. 如何定义符合 error-first 约定的异步函数
 *   2. 调用方如何正确处理 err 与 data
 *   3. 错误必须显式处理，不能"吞掉"
 */

'use strict';

/**
 * 模拟异步读取用户信息（类似数据库查询）
 * @param {number} userId - 用户 ID
 * @param {(err: Error|null, user?: object) => void} callback - 错误优先回调
 */
function fetchUser(userId, callback) {
  // 用 setTimeout 模拟 I/O 延迟（100ms）
  setTimeout(() => {
    // 模拟异常情况：用户 ID 不存在
    if (userId <= 0) {
      // 错误优先：第一个参数传 Error 对象
      return callback(new Error(`用户 ID 非法：${userId}`));
    }

    // 模拟数据库中的用户表
    const users = {
      1: { id: 1, name: '张三', role: 'admin' },
      2: { id: 2, name: '李四', role: 'member' },
      3: { id: 3, name: '王五', role: 'guest' },
    };

    const user = users[userId];
    if (!user) {
      // 找不到用户也是错误
      return callback(new Error(`未找到 ID 为 ${userId} 的用户`));
    }

    // 成功：第一个参数为 null，第二个参数为数据
    callback(null, user);
  }, 100);
}

/**
 * 错误优先回调的"标准"调用方式
 */
function main() {
  console.log('--- 错误优先回调示例 ---\n');

  // 情况 1：成功读取
  console.log('1) 尝试读取 ID = 2 的用户...');
  fetchUser(2, (err, user) => {
    if (err) {
      // 必须显式检查 err，否则异常会被"吞掉"
      console.error('   ❌ 失败:', err.message);
      return;
    }
    console.log('   ✅ 成功:', user);
  });

  // 情况 2：非法 ID
  console.log('2) 尝试读取 ID = 0 的用户...');
  fetchUser(0, (err, user) => {
    if (err) {
      console.error('   ❌ 失败:', err.message);
      return;
    }
    console.log('   ✅ 成功:', user);
  });

  // 情况 3：不存在的用户
  console.log('3) 尝试读取 ID = 99 的用户...');
  fetchUser(99, (err, user) => {
    if (err) {
      console.error('   ❌ 失败:', err.message);
      return;
    }
    console.log('   ✅ 成功:', user);
  });

  console.log('\n（注意：以上输出顺序由 setTimeout 决定，会在 100ms 后一起到达）\n');
}

main();

/**
 * 运行方式：
 *   node callback-demo.js
 *
 * 预期输出（顺序可能略有不同）：
 *   --- 错误优先回调示例 ---
 *
 *   1) 尝试读取 ID = 2 的用户...
 *   2) 尝试读取 ID = 0 的用户...
 *   3) 尝试读取 ID = 99 的用户...
 *
 *   （注意：以上输出顺序由 setTimeout 决定，会在 100ms 后一起到达）
 *
 *      ❌ 失败: 用户 ID 非法：0
 *      ✅ 成功: { id: 2, name: '李四', role: 'member' }
 *      ❌ 失败: 未找到 ID 为 99 的用户
 *
 * 关键点：
 *   - 回调的第一个参数永远是 err，成功时为 null
 *   - 必须用 if (err) 检查，不能直接用 data
 *   - 错误处理与正常流程分离，避免吞错
 */
