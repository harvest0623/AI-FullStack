/**
 * Day13 - 类型体操实战 07：对象路径 Path<T> 与类型安全 get
 *
 * 本文件实现两个互相关联的高阶类型体操：
 * 1. Path<T>        ：根据对象结构生成所有“点分路径”联合（如 'a' | 'a.b' | 'a.b.c'）
 * 2. Get<T, P>      ：根据路径字符串反推对应值的类型
 * 3. get(obj, path) ：运行时函数，路径与返回值都类型安全
 *
 * 这是 lodash.get / ramda.path 等库的“类型加强版”核心模型，
 * 综合用到：递归条件类型 + 模板字面量 + infer + 映射类型。
 */

export {};

// ============================================================
// 1. Path<T>：生成所有点分路径
// ============================================================

// 思路：递归遍历对象的每个键
//  - 基线：基础类型（非对象）→ 没有子路径，返回 never
//  - 递归：对每个键 K，生成 K 本身 + `${K}.${子路径}`
//  - 排除：null / 数组 / 函数（避免生成不合理的路径）
type Path<T, Depth extends number = 5> = [Depth] extends [0]
  ? never
  : T extends object
    ? T extends Array<any>
      ? never                                   // 数组不递归（简化处理）
      : T extends (...args: any[]) => any
        ? never                                 // 函数不递归
        : {
            [K in keyof T & string]:
              | K                                // 键本身（一级路径）
              | `${K}.${Path<T[K], Decrement<Depth>>}`;   // 键 + 子路径
          }[keyof T & string]
    : never;

// Decrement：递归深度计数器（防止无限递归）
// 用元组长度做减法：[unknown, unknown, ...][n] 取前 n 个
type Decrement<N extends number> = N extends 5 ? 4
  : N extends 4 ? 3
  : N extends 3 ? 2
  : N extends 2 ? 1
  : N extends 1 ? 0
  : 0;

// 演示
interface TreeNode {
  id: number;
  profile: {
    name: string;
    contact: {
      email: string;
      phone: string;
    };
  };
  tags: string[];
}

type TreeNodePaths = Path<TreeNode>;
// 'id' | 'profile' | 'profile.name' | 'profile.contact' |
// 'profile.contact.email' | 'profile.contact.phone' | 'tags'

// 类型层面验证：把路径列出
const allPaths: TreeNodePaths[] = [
  'id',
  'profile',
  'profile.name',
  'profile.contact',
  'profile.contact.email',
  'profile.contact.phone',
  'tags',
];
console.log('[Path] 所有路径 =>', allPaths);


// ============================================================
// 2. Get<T, P>：根据路径反推值类型
// ============================================================

// 思路：把路径字符串按 '.' 切分，逐层索引访问
//  - P = `${infer Head}.${infer Tail}` → 递归 Get<T[Head], Tail>
//  - P = 单个键 → T[P]
//  - 越界或不存在 → never（TS 会保留 never 提示错误）
type Get<T, P extends string> =
  P extends `${infer Head}.${infer Tail}`
    ? Head extends keyof T
      ? Get<T[Head], Tail>
      : never
    : P extends keyof T
      ? T[P]
      : never;

type V1 = Get<TreeNode, 'id'>;                          // number
type V2 = Get<TreeNode, 'profile.name'>;                // string
type V3 = Get<TreeNode, 'profile.contact.email'>;       // string
type V4 = Get<TreeNode, 'profile.contact'>;             // { email: string; phone: string }
type V5 = Get<TreeNode, 'tags'>;                        // string[]

console.log('[Get] 类型推断 =>',
  0 as V1, '|', '' as V2, '|', '' as V3, '|', [] as V5);


// ============================================================
// 3. 类型安全的 get 函数（运行时）
// ============================================================

/**
 * 按 'a.b.c' 路径安全取值，路径与返回类型都强校验
 *  - 路径必须是 Path<T> 的成员（不存在会编译报错）
 *  - 返回值类型由 Get<T, P> 自动推断
 *  - 运行时遇到 undefined 不会抛错，返回 undefined
 */
function get<T extends object, P extends Path<T>>(
  obj: T,
  path: P,
): Get<T, P> | undefined {
  const segments = path.split('.');
  let current: any = obj;
  for (const seg of segments) {
    if (current == null) return undefined;
    current = current[seg];
  }
  return current as Get<T, P>;
}

const tree: TreeNode = {
  id: 1,
  profile: {
    name: 'Alice',
    contact: { email: 'a@x.com', phone: '13800000000' },
  },
  tags: ['ts', 'js'],
};

// ✅ 路径合法 + 返回类型自动推断为 number
const id = get(tree, 'id');
console.log('[get] id =>', id);

// ✅ 嵌套路径，返回类型为 string
const email = get(tree, 'profile.contact.email');
console.log('[get] email =>', email);

// ✅ 返回对象
const contact = get(tree, 'profile.contact');
console.log('[get] contact =>', contact);

// ✅ 返回数组
const tags = get(tree, 'tags');
console.log('[get] tags =>', tags);

// ❌ 以下调用都会编译报错：
// get(tree, 'name');                  // 不在顶层
// get(tree, 'profile.unknown');       // 不存在的键
// get(tree, 'profile.contact.email.x'); // email 是 string，无子键


// ============================================================
// 4. 容错场景：中间字段可能为 undefined
// ============================================================

// 当对象中存在可选字段时，Get 会保留 undefined
interface MaybeTree {
  a?: {
    b?: {
      c: string;
    };
  };
}

type MaybePaths = Path<MaybeTree>;
// 'a' | 'a.b' | 'a.b.c'

// 这里 Get 返回类型会包含 undefined（因为 a / b 可选）
type MaybeC = Get<MaybeTree, 'a.b.c'>;
// string | undefined

const mt: MaybeTree = { a: { b: { c: 'hi' } } };
const cVal = get(mt as Required<MaybeTree>, 'a.b.c');
console.log('[容错 get] =>', cVal);


// ============================================================
// 5. 进阶：PathAndValue<T> —— 路径 + 值 的元组联合
// ============================================================

// 一次性生成“所有路径与其对应值类型”的元组联合
type PathAndValue<T, P extends Path<T> = Path<T>> = P extends any
  ? [path: P, value: Get<T, P>]
  : never;

type PV = PathAndValue<TreeNode>;
// ['id', number] | ['profile', {...}] | ['profile.name', string] | ...

// 用途：编写“遍历所有路径并处理值”的工具时，能获得完整类型信息
function walk<T extends object>(obj: T, visitor: (path: Path<T>, value: Get<T, Path<T>>) => void) {
  // 简化实现：仅遍历两层
  for (const k of Object.keys(obj) as (keyof T & string)[]) {
    visitor(k as any, obj[k] as any);
    const sub = obj[k];
    if (sub && typeof sub === 'object' && !Array.isArray(sub)) {
      for (const k2 of Object.keys(sub) as (string[])) {
        visitor(`${k}.${k2}` as any, (sub as any)[k2]);
      }
    }
  }
}

walk(tree, (p, v) => {
  console.log('[walk] ', p, '=>', typeof v === 'object' ? JSON.stringify(v) : v);
});


// ============================================================
// 6. 进阶：IsEqual<A, B> —— 类型层面判等
// ============================================================

// TS 的条件类型 A extends B 在“联合”场景下会分发，无法直接判等
// 经典 hack：用 [A, B] 与 [B, A] 的双向 extends 判等
type IsEqual<A, B> =
  [A] extends [B]
    ? [B] extends [A]
      ? true
      : false
    : false;

type E1 = IsEqual<string, string>;          // true
type E2 = IsEqual<string, number>;          // false
type E3 = IsEqual<'a' | 'b', 'a' | 'b'>;    // true
type E4 = IsEqual<string, string | number>; // false（注意：不是 true）
type E5 = IsEqual<any, string>;             // false（any 的特殊性，IsEqual 特意拒绝）

console.log('[IsEqual] =>',
  true as E1, '|', false as E2, '|', true as E3, '|', false as E4, '|', false as E5);


console.log('\n--- object-path.ts 执行完毕 ---');
