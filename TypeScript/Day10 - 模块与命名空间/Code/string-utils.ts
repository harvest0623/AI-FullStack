/**
 * Day10 - string-utils.ts
 *
 * 另一个工具模块，同样演示「命名导出 + 默认导出 + 类型导出」。
 * 与 math-utils.ts 一起被 index.ts 聚合 re-export。
 */

// ============================================================
// 1. 类型导出
// ============================================================

/** 字符串大小写模式 */
export type StringCase = 'upper' | 'lower' | 'title';

/** 截断选项 */
export interface TruncateOptions {
  /** 最大长度 */
  maxLength: number;
  /** 省略号，默认 "..." */
  ellipsis?: string;
}

// ============================================================
// 2. 命名导出
// ============================================================

export function capitalize(s: string): string {
  return s.length === 0 ? s : s[0].toUpperCase() + s.slice(1);
}

export function truncate(s: string, options: TruncateOptions): string {
  const ellipsis = options.ellipsis ?? '...';
  if (s.length <= options.maxLength) return s;
  const cut = Math.max(0, options.maxLength - ellipsis.length);
  return s.slice(0, cut) + ellipsis;
}

/** 按模式转换大小写，演示 StringCase 字面量联合的分发 */
export function toCase(s: string, c: StringCase): string {
  switch (c) {
    case 'upper': return s.toUpperCase();
    case 'lower': return s.toLowerCase();
    case 'title': return s.split(' ').map(capitalize).join(' ');
  }
}

/** 把任意字符串转为 URL slug */
export function slugify(s: string): string {
  return s
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

// ============================================================
// 3. 默认导出
// ============================================================

const stringToolkit = { capitalize, truncate, toCase, slugify };
export default stringToolkit;

// ============================================================
// 4. 运行时演示
// ============================================================

if (require.main === module) {
  console.log('capitalize("hello") =', capitalize('hello'));
  console.log('truncate =', truncate('一二三四五六七八九十', { maxLength: 6, ellipsis: '…' }));
  console.log('toCase("hello world", "title") =', toCase('hello world', 'title'));
  console.log('slugify(" Hello, World! ") =', slugify(' Hello, World! '));
  console.log('\n--- string-utils.ts 执行完毕 ---');
}
