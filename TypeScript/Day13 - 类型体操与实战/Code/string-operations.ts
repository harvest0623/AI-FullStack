/**
 * Day13 - 类型体操实战 04：模板字面量类型与字符串操作
 *
 * 本文件实现字符串层面的类型体操，全部基于“模板字面量类型 + infer 模式匹配 + 递归”：
 * 1. Join<T, Sep>      ：用分隔符拼接字符串元组
 * 2. Split<S, Sep>     ：按分隔符切分字符串为元组（Join 的对偶）
 * 3. CamelCase<S>      ：snake/kebab → camelCase
 * 4. KebabCase<S>      ：camel/snake → kebab-case
 * 5. SnakeCase<S>      ：camel/kebab → snake_case
 * 6. Replace<S, From, To>   ：替换首次出现
 * 7. ReplaceAll<S, From, To>：递归替换所有
 *
 * 核心套路：用 `S extends \`${infer Head}<Sep>${infer Tail}\`` 做模式匹配，
 * 匹配成功则递归处理 Tail，否则原样返回。
 */

export {};

// ============================================================
// 1. Join<T, Sep>：拼接字符串元组
// ============================================================

// 思路：递归取出元组首元素，与分隔符 + 剩余拼接结果合并
//  - [infer F, ...infer R]  解构首元素和剩余
//  - R 是空元组时停止递归（不再加分隔符）
type Join<T extends readonly string[], Sep extends string> =
  T extends readonly [infer F extends string, ...infer R extends string[]]
    ? R extends []
      ? F
      : `${F}${Sep}${Join<R, Sep>}`
    : '';

type J1 = Join<['a', 'b', 'c'], '-'>;     // 'a-b-c'
type J2 = Join<['hello'], '.'>;            // 'hello'
type J3 = Join<[], '/'>;                   // ''
type J4 = Join<['x', 'y', 'z'], '/'>;      // 'x/y/z'

const j1: J1 = 'a-b-c';
const j2: J2 = 'hello';
const j3: J3 = '';
const j4: J4 = 'x/y/z';
console.log('[Join] =>', { j1, j2, j3, j4 });


// ============================================================
// 2. Split<S, Sep>：切分字符串为元组
// ============================================================

// 思路：用 infer 模式匹配 `${Head}<Sep>${Tail}`
//  - 匹配成功 → 把 Head 放入元组，递归处理 Tail
//  - 不匹配   → 字符串无 Sep，整体作为唯一元素
type Split<S extends string, Sep extends string> =
  S extends `${infer Head}${Sep}${infer Tail}`
    ? [Head, ...Split<Tail, Sep>]
    : S extends ''
      ? []
      : [S];

type S1 = Split<'a-b-c', '-'>;            // ['a', 'b', 'c']
type S2 = Split<'hello.world', '.'>;      // ['hello', 'world']
type S3 = Split<'single', '-'>;           // ['single']
type S4 = Split<'', '-'>;                 // []

const s1: S1 = ['a', 'b', 'c'];
const s2: S2 = ['hello', 'world'];
const s3: S3 = ['single'];
const s4: S4 = [];
console.log('[Split] =>', { s1, s2, s3, s4 });


// ============================================================
// 3. CamelCase<S>：snake_case / kebab-case → camelCase
// ============================================================

// 思路：匹配 `${Head}_/-${Char}${Tail}`
//  - 把分隔符后的首个字符大写：`${Head}${Uppercase<Char>}${递归 Tail}`
//  - 不匹配 → 原样返回（已是最终形式）
//  注意：首字母不强转为小写（首字母大小写由输入决定），如需 PascalCase 单独处理
type CamelCase<S extends string> =
  S extends `${infer Head}_${infer Char}${infer Tail}`
    ? `${Head}${Uppercase<Char>}${CamelCase<Tail>}`
    : S extends `${infer Head}-${infer Char}${infer Tail}`
      ? `${Head}${Uppercase<Char>}${CamelCase<Tail>}`
      : S;

type C1 = CamelCase<'user_id_card'>;      // 'userIdCard'
type C2 = CamelCase<'my-var-name'>;       // 'myVarName'
type C3 = CamelCase<'simple'>;            // 'simple'
type C4 = CamelCase<'a_b_c_d'>;           // 'aBCD'

const c1: C1 = 'userIdCard';
const c2: C2 = 'myVarName';
console.log('[CamelCase] =>', { c1, c2 });


// ============================================================
// 4. KebabCase<S>：camelCase / snake_case → kebab-case
// ============================================================

// 思路：逐字符扫描，遇大写字母前插入 '-'
//  - 用线性递归（每次只推进一位）避免指数级复杂度
//  - 大写字母判断：Upper extends Uppercase<Upper> 且 Upper extends Lowercase<Upper> 不成立
//    （数字/符号大小写相等，借此排除）
//  - 用 DropLeadingSep 去掉首字符可能产生的前导 '-'
type DropLeadingSep<S extends string, Sep extends string> =
  S extends `${Sep}${infer R}` ? R : S;

type KebabCaseImpl<S extends string> =
  S extends `${infer First}${infer Rest}`
    ? First extends Uppercase<First>
      ? First extends Lowercase<First>           // 数字/符号（大小写相等）
        ? `${First}${KebabCaseImpl<Rest>}`        // 不分词
        : `-${Lowercase<First>}${KebabCaseImpl<Rest>}`  // 大写字母：前加 -
      : `${First}${KebabCaseImpl<Rest>}`          // 小写字母：原样拼接
    : S;

type KebabCase<S extends string> = DropLeadingSep<KebabCaseImpl<S>, '-'>;

type K1 = KebabCase<'userIdCard'>;        // 'user-id-card'
type K2 = KebabCase<'myVarName'>;         // 'my-var-name'
type K3 = KebabCase<'simple'>;            // 'simple'
type K4 = KebabCase<'HTMLParser'>;        // 'h-t-m-l-parser'（连续大写会逐个分词）

const k1: K1 = 'user-id-card';
const k2: K2 = 'my-var-name';
console.log('[KebabCase] =>', { k1, k2, k4: '' as K4 });


// ============================================================
// 5. SnakeCase<S>：camelCase / kebab-case → snake_case
// ============================================================

// 与 KebabCase 同构，只是分隔符换成 '_'
type SnakeCaseImpl<S extends string> =
  S extends `${infer First}${infer Rest}`
    ? First extends Uppercase<First>
      ? First extends Lowercase<First>
        ? `${First}${SnakeCaseImpl<Rest>}`
        : `_${Lowercase<First>}${SnakeCaseImpl<Rest>}`
      : `${First}${SnakeCaseImpl<Rest>}`
    : S;

type SnakeCase<S extends string> = DropLeadingSep<SnakeCaseImpl<S>, '_'>;

type SC1 = SnakeCase<'userIdCard'>;       // 'user_id_card'
type SC2 = SnakeCase<'my-var-name'>;      // 'my_var_name'（'-' 保留为 '-'，需另外处理）

// 处理 '-' 分隔：先用 ReplaceAll 把 '-' 转成 '_'，再走 SnakeCase
type ReplaceAll<S extends string, From extends string, To extends string> =
  S extends `${infer Before}${From}${infer After}`
    ? `${Before}${To}${ReplaceAll<After, From, To>}`
    : S;

type SC3 = SnakeCase<ReplaceAll<'my-var-name', '-', '_'>>;  // 'my_var_name'
type SC4 = SnakeCase<'simple'>;           // 'simple'

const sc1: SC1 = 'user_id_card';
const sc3: SC3 = 'my_var_name';
console.log('[SnakeCase] =>', { sc1, sc3 });


// ============================================================
// 6. Replace / ReplaceAll：字符串替换
// ============================================================

// 只替换首次出现
type Replace<
  S extends string,
  From extends string,
  To extends string,
> = S extends `${infer Before}${From}${infer After}`
  ? `${Before}${To}${After}`
  : S;

// 递归替换所有
// ReplaceAll 已在上方定义，这里直接使用

type R1 = Replace<'hello world', 'world', 'TS'>;         // 'hello TS'
type R2 = ReplaceAll<'a-b-c-d', '-', '_'>;               // 'a_b_c_d'
type R3 = ReplaceAll<'foo bar foo', 'foo', 'FOO'>;       // 'FOO bar FOO'

const r1: R1 = 'hello TS';
const r2: R2 = 'a_b_c_d';
const r3: R3 = 'FOO bar FOO';
console.log('[Replace] =>', { r1, r2, r3 });


// ============================================================
// 7. 综合实战：批量重命名键 + 路径生成
// ============================================================

interface UserSnake {
  user_id: number;
  user_name: string;
  is_active: boolean;
}

// 场景 1：把 snake_case 的接口转成 camelCase 版本
// 用映射类型 + as 重映射 + CamelCase 工具
type CamelCaseKeys<T> = {
  [K in keyof T as K extends string ? CamelCase<K> : K]: T[K];
};

type UserCamel = CamelCaseKeys<UserSnake>;
// { userId: number; userName: string; isActive: boolean }

const userCamel: UserCamel = { userId: 1, userName: 'Alice', isActive: true };
console.log('[实战 CamelCaseKeys] =>', userCamel);

// 场景 2：从联合生成所有“带前缀的常量名”
type Action = 'create' | 'update' | 'delete';
type ConstantName = `ACTION_${Uppercase<Action>}`;
// 'ACTION_CREATE' | 'ACTION_UPDATE' | 'ACTION_DELETE'

const act: ConstantName = 'ACTION_CREATE';
console.log('[实战 模板拼接] =>', act);

// 场景 3：把字符串元组拼成 SQL 列定义
type Columns = ['id', 'name', 'email'];
type ColumnList = Join<Columns, ', '>;
// 'id, name, email'

const cols: ColumnList = 'id, name, email';
console.log('[实战 Join SQL] =>', `SELECT ${cols} FROM users`);


console.log('\n--- string-operations.ts 执行完毕 ---');
