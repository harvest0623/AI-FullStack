/**
 * 模块系统：ES Modules（.mjs 扩展名强制为 ESM，与 package.json 无关）
 *
 * 演示点：
 * 1. 命名导出：area、circumference、PI
 * 2. 默认导出：一个聚合对象
 * 3. import.meta.url：获取当前模块的 file:// URL
 * 4. 在 ESM 中通过 import.meta.url 派生 __dirname / __filename
 */

import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';

// 常量（命名导出）
export const PI = 3.14159;

// 命名导出：圆面积
export function area(radius) {
  return PI * radius * radius;
}

// 命名导出：圆周长
export function circumference(radius) {
  return 2 * PI * radius;
}

// 默认导出：聚合对象（一个模块只能有一个默认导出）
export default {
  area,
  circumference,
  PI,
  description: 'circle-area 默认导出的聚合对象',
};

// import.meta.url 演示
console.log('[circle-area] import.meta.url =', import.meta.url);

// 在 ESM 中模拟 __dirname / __filename（ESM 没有这两个全局变量）
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
console.log('[circle-area] 派生 __filename =', __filename);
console.log('[circle-area] 派生 __dirname  =', __dirname);
