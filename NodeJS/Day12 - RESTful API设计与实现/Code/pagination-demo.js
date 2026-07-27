/**
 * 分页逻辑单独演示
 *
 * 运行：node pagination-demo.js
 *
 * 本文件脱离 Express，单独演示 page/pageSize 的计算与边界处理，
 * 帮助你理解“分页响应”背后的数学逻辑。
 */

// 模拟 27 条数据
const items = Array.from({ length: 27 }, (_, i) => ({
  id: i + 1,
  name: `item-${i + 1}`,
}));

/**
 * 通用分页函数
 * @param {Array} data - 全量数据
 * @param {number} [page=1] - 当前页（从 1 开始）
 * @param {number} [pageSize=10] - 每页条数
 * @returns {{ list: Array, total: number, page: number, pageSize: number, totalPages: number }}
 */
function paginate(data, page = 1, pageSize = 10) {
  const total = data.length;

  // 每页条数至少为 1，防止除零
  const safePageSize = Math.max(1, pageSize);

  // 总页数（向上取整），total 为 0 时 totalPages 至少为 1，避免除零
  const totalPages = Math.max(1, Math.ceil(total / safePageSize));

  // 边界处理：page 限制在 [1, totalPages] 区间
  const safePage = Math.max(1, Math.min(page, totalPages));

  // 计算起始索引（页码从 1 开始，所以减 1）
  const start = (safePage - 1) * safePageSize;

  // 切片取当前页数据
  const list = data.slice(start, start + safePageSize);

  return { list, total, page: safePage, pageSize: safePageSize, totalPages };
}

// ---------------------------------------------------------------------------
// 演示场景
// ---------------------------------------------------------------------------

function printResult(label, result) {
  const ids = result.list.map((item) => item.id).join(', ');
  console.log(
    `${label}：\n  page=${result.page}, pageSize=${result.pageSize}, ` +
      `total=${result.total}, totalPages=${result.totalPages}, ` +
      `list=[${ids}] (${result.list.length} 条)\n`
  );
}

console.log('=== 分页演示（共 27 条数据）===\n');

// 正常场景
printResult('第 1 页（pageSize=10）', paginate(items, 1, 10));
printResult('第 2 页（pageSize=10）', paginate(items, 2, 10));
printResult('第 3 页（pageSize=10，最后一页只有 7 条）', paginate(items, 3, 10));

// 边界场景：页码超出
printResult('第 4 页（超出总页数，自动回到第 3 页）', paginate(items, 4, 10));

// 边界场景：非法页码
printResult('page=0（非法，自动修正为 1）', paginate(items, 0, 10));
printResult('page=-5（负数，自动修正为 1）', paginate(items, -5, 10));
printResult('page="abc"（非数字，parseInt 失败回退默认 1）', paginate(items, parseInt('abc', 10) || 1, 10));

// 调整 pageSize
printResult('pageSize=5，第 3 页', paginate(items, 3, 5));
printResult('pageSize=20，第 1 页', paginate(items, 1, 20));
printResult('pageSize=100（超出数据量，返回全部）', paginate(items, 1, 100));

// 空数据场景
printResult('空数据分页', paginate([], 1, 10));

// ---------------------------------------------------------------------------
// 边界处理要点总结
// ---------------------------------------------------------------------------

console.log('=== 边界处理要点 ===');
console.log('1. page 最小为 1，非法值（0、负数、非数字）回退到 1');
console.log('2. pageSize 最小为 1，实际项目应设上限（如 100）防止拖垮服务');
console.log('3. page 超出总页数时，自动回到最后一页（也可选择返回空列表）');
console.log('4. total 为 0 时 totalPages 至少为 1，避免除零错误');
console.log('5. 切片用 Array.slice，天然处理越界（越界返回空数组，不报错）');
