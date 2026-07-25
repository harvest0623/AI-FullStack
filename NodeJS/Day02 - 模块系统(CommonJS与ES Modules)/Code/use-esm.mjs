/**
 * 模块系统：ES Modules（.mjs）
 *
 * 演示点：三种导入方式
 * 1. 命名导入：import { area, circumference } from './circle-area.mjs'
 * 2. 默认导入：import circleDefault from './circle-area.mjs'
 * 3. 命名空间导入：import * as circleNs from './circle-area.mjs'
 *
 * 注意：ESM 中导入相对路径必须带完整扩展名（.mjs），Node 18+ 强制要求。
 */

// 1. 命名导入：只引入需要的命名导出
import { area, circumference, PI } from './circle-area.mjs';

// 2. 默认导入：引入 default 导出，名字可自定义
import circleDefault from './circle-area.mjs';

// 3. 命名空间导入：把整个模块作为一个对象
import * as circleNs from './circle-area.mjs';

console.log('=== 1. 命名导入调用 ===');
console.log('area(2)          =', area(2));
console.log('circumference(2) =', circumference(2));
console.log('PI               =', PI);

console.log('\n=== 2. 默认导入调用 ===');
console.log('circleDefault =', circleDefault);
console.log('circleDefault.area(3) =', circleDefault.area(3));

console.log('\n=== 3. 命名空间导入调用 ===');
console.log('circleNs.area(4)        =', circleNs.area(4));
console.log('circleNs.circumference(4) =', circleNs.circumference(4));
console.log('circleNs.default        =', circleNs.default); // 默认导出挂在 .default 上
console.log('circleNs.PI             =', circleNs.PI);

console.log('\n=== 4. 当前模块的 import.meta.url ===');
console.log(import.meta.url);
