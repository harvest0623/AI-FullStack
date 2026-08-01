/**
 * Day13 - 类型体操实战 05：类型安全的路由系统
 *
 * 本文件演示如何用模板字面量类型 + infer 从路由字符串中提取参数，
 * 并实现一个“路由 → params 类型自动推断”的类型安全路由器。
 *
 * 核心难点：
 * 1. 从 '/users/:id' 提取 'id' 键
 * 2. 处理多参数 '/posts/:postId/comments/:commentId'
 * 3. 把参数键联合构造成 { id: string; postId: string; ... } 的 params 对象类型
 * 4. 运行时正确解析路径并校验类型
 */

export {};

// ============================================================
// 1. 提取路由参数键
// ============================================================

// 思路：递归扫描路径字符串，匹配 `:name` 形式的参数
//  - `${infer _Pre}:${infer Param}/${infer Rest}`  匹配带斜杠的参数（中间参数）
//  - `${infer _Pre}:${infer Param}`                匹配末尾参数（无后续斜杠）
//  - 每次提取一个 Param，加入联合，递归处理剩余
type ExtractRouteParams<S extends string> =
  S extends `${infer _Pre}:${infer Param}/${infer Rest}`
    ? Param | ExtractRouteParams<`/${Rest}`>
    : S extends `${infer _Pre}:${infer Param}`
      ? Param
      : never;

type P1 = ExtractRouteParams<'/users/:id'>;
// 'id'
type P2 = ExtractRouteParams<'/posts/:postId/comments/:commentId'>;
// 'postId' | 'commentId'
type P3 = ExtractRouteParams<'/home'>;
// never（无参数）
type P4 = ExtractRouteParams<'/files/:dir/:subdir/:file'>;
// 'dir' | 'subdir' | 'file'

console.log('[ExtractRouteParams] P1 =>', '' as P1);
console.log('[ExtractRouteParams] P2 =>', '' as P2);


// ============================================================
// 2. 构造 params 对象类型
// ============================================================

// 把参数键联合映射为 { [K in Params]: string } 形式
//  - never 时返回空对象（用 Record<never, string> 会得到 {}）
type RouteParams<S extends string> = {
  [K in ExtractRouteParams<S>]: string;
};

type Params1 = RouteParams<'/users/:id'>;
// { id: string }
type Params2 = RouteParams<'/posts/:postId/comments/:commentId'>;
// { postId: string; commentId: string }
type Params3 = RouteParams<'/home'>;
// {} （无参数）

const params1: Params1 = { id: '42' };
const params2: Params2 = { postId: '1', commentId: '2' };
const params3: Params3 = {};
console.log('[RouteParams] =>', { params1, params2, params3 });


// ============================================================
// 3. 类型安全的路由定义与匹配
// ============================================================

// 路由处理器类型：根据路径自动推断 handler 接收的 params 类型
type RouteHandler<Path extends string> = (params: RouteParams<Path>) => void;

// 路由表：一组路径 → 处理器
class Router {
  private routes: { path: string; handler: (params: Record<string, string>) => void }[] = [];

  // 注册路由：Path 是字面量类型，params 类型自动推断
  add<Path extends string>(path: Path, handler: RouteHandler<Path>): this {
    this.routes.push({ path, handler: handler as (p: Record<string, string>) => void });
    return this;
  }

  // 匹配并触发：运行时把路径解析为 params，调用对应 handler
  match(fullPath: string): boolean {
    for (const route of this.routes) {
      const params = this.matchRoute(route.path, fullPath);
      if (params !== null) {
        route.handler(params);
        return true;
      }
    }
    return false;
  }

  // 把 path 模式（含 :param）转为正则，与 fullPath 匹配后回填 params
  private matchRoute(pattern: string, fullPath: string): Record<string, string> | null {
    const paramNames: string[] = [];
    // 转正则：把 :name 替换为 ([^/]+) 捕获组
    const regexStr = pattern.replace(/:([^/]+)/g, (_, name: string) => {
      paramNames.push(name);
      return '([^/]+)';
    });
    const regex = new RegExp(`^${regexStr}$`);
    const match = fullPath.match(regex);
    if (!match) return null;

    const params: Record<string, string> = {};
    paramNames.forEach((name, i) => {
      params[name] = match[i + 1];
    });
    return params;
  }
}

// ============================================================
// 4. 实战：注册并触发路由
// ============================================================

const router = new Router();

router
  .add('/users/:id', (params) => {
    // ✅ params 类型自动推断为 { id: string }
    console.log('[路由] GET /users/:id =>', `用户ID: ${params.id}`);
    // params.postId;  // ❌ 不存在该属性
  })
  .add('/posts/:postId/comments/:commentId', (params) => {
    // ✅ params 类型自动推断为 { postId: string; commentId: string }
    console.log('[路由] GET /posts/:postId/comments/:commentId =>',
      `文章 ${params.postId} 评论 ${params.commentId}`);
  })
  .add('/home', (params) => {
    // ✅ params 类型为 {} （无参数）
    console.log('[路由] GET /home => 首页');
  });

// 触发匹配
router.match('/users/42');
router.match('/posts/1/comments/99');
router.match('/home');
router.match('/not-exist');   // 不匹配任何路由，无输出


// ============================================================
// 5. 进阶：编译期校验路由路径合法性
// ============================================================

// 约束路径必须以 '/' 开头
type ValidPath<S extends string> = S extends `/${string}` ? S : never;

function defineRoute<S extends string>(path: ValidPath<S> & string): S {
  return path;
}

const r1 = defineRoute('/users/:id');       // ✅
// const r2 = defineRoute('users/:id');     // ❌ 不以 '/' 开头
console.log('[defineRoute] =>', r1);


// ============================================================
// 6. 进阶：路径 → HTTP 方法 → 完整接口描述
// ============================================================

// 把方法和路径联合成接口名：'GET /users/:id' 形式
type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
type Endpoint<M extends HttpMethod, P extends string> = `${M} ${P}`;

type ApiEndpoint = Endpoint<'GET', '/users/:id'>;
// 'GET /users/:id'

const ep: ApiEndpoint = 'GET /users/:id';
console.log('[Endpoint] =>', ep);

// 类型安全的路由分发器：根据完整接口名查 params 类型
type ApiMap = {
  'GET /users/:id': { id: string };
  'GET /posts/:postId/comments/:commentId': { postId: string; commentId: string };
  'POST /users': {};        // 无参数
};

function dispatch<K extends keyof ApiMap>(
  endpoint: K,
  params: ApiMap[K],
): void {
  console.log('[dispatch]', endpoint, '=> params:', params);
}

dispatch('GET /users/:id', { id: '42' });
dispatch('GET /posts/:postId/comments/:commentId', { postId: '1', commentId: '2' });
dispatch('POST /users', {});
// dispatch('GET /users/:id', {});   // ❌ 缺少 id
// dispatch('GET /unknown', {});     // ❌ 不在 ApiMap 中


console.log('\n--- type-safe-router.ts 执行完毕 ---');
