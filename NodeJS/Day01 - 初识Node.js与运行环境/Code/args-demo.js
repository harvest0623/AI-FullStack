/**
 * Day01 练习三：args-demo.js
 * 命令行参数读取与求和
 *
 * 学习要点：
 *   1. process.argv 的结构：[node 路径, 脚本路径, 用户参数1, 用户参数2, ...]
 *   2. 用 slice(2) 跳过前两项，拿到真正的用户输入
 *   3. 字符串转数字（Number）与非法值的过滤
 *   4. 对「无参数」场景做友好提示
 *
 * 运行方式：
 *   node args-demo.js 10 20 30
 *   node args-demo.js 1.5 2.5 3
 *   node args-demo.js
 */

// process.argv 形如：['D:\\node.exe', 'D:\\args-demo.js', '10', '20', '30']
// 用 slice(2) 截取从索引 2 开始的所有元素，即用户传入的参数
const rawArgs = process.argv.slice(2);

// 无参数场景：给出使用提示并退出
if (rawArgs.length === 0) {
  console.log('未传入任何数字参数。');
  console.log('用法：node args-demo.js <数字1> <数字2> ... ');
  console.log('示例：node args-demo.js 10 20 30');
  // 以非 0 状态码退出，表示「未正常产生结果」
  process.exit(0);
}

// 打印原始接收到的参数（字符串数组）
console.log(`接收到的参数：[ ${rawArgs.map((s) => `'${s}'`).join(', ')} ]`);

// 将每个字符串参数转换为数字
// Number('abc') 会得到 NaN，用 Number.isFinite 过滤掉非法值
const numbers = rawArgs.map((s) => Number(s)).filter((n) => Number.isFinite(n));

// 解析后若没有有效数字，同样提示
if (numbers.length === 0) {
  console.log('解析为数字：[]（未识别到任何有效数字）');
  process.exit(0);
}

// 打印解析后的数字数组
console.log(`解析为数字：[ ${numbers.join(', ')} ]`);

// 求和：用 reduce 累加，初始值 0
const sum = numbers.reduce((acc, cur) => acc + cur, 0);

// 拼接计算过程，如 "10 + 20 + 30 = 60"
const expression = numbers.join(' + ');
console.log(`求和结果：${expression} = ${sum}`);
