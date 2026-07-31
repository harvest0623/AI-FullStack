/**
 * Day08 - 模板字面量类型 Template Literal Types
 *
 * 本文件演示：
 * 1. 基本拼接 `${prefix}${string}`
 * 2. Uppercase / Lowercase / Capitalize / Uncapitalize 在模板中的应用
 * 3. 结合 keyof + as 生成 getter / setter 名
 * 4. 实战模式：路由表 / 事件名 / CSS 类名
 */

export {};

// ============================================================
// 1. 基本拼接
// ============================================================

// 把字符串字面量拼接成新的字面量类型
type Greeting = `hello ${string}`;
// 匹配任意以 "hello " 开头的字符串

const g1: Greeting = 'hello world';
const g2: Greeting = 'hello typescript';
// const g3: Greeting = 'hi world';   // ❌ 不以 "hello " 开头
console.log('[基础] Greeting =>', g1, '|', g2);


// 多个字面量联合拼接：笛卡尔积
type Side   = 'top' | 'right' | 'bottom' | 'left';
type Margin = `margin-${Side}`;
// 'margin-top' | 'margin-right' | 'margin-bottom' | 'margin-left'

const m: Margin = 'margin-top';
console.log('[基础] Margin =>', m);

type Size  = 'sm' | 'md' | 'lg';
type Color = 'primary' | 'secondary' | 'danger';
type BtnClass = `btn-${Size}-${Color}`;
// 'btn-sm-primary' | 'btn-sm-secondary' | ... 共 9 种

const bc: BtnClass = 'btn-lg-danger';
console.log('[基础] BtnClass =>', bc);


// 用 ${string} 占位通配任意后缀
type HTTPEndpoint = `/api/${string}`;
const ep: HTTPEndpoint = '/api/users/123';
console.log('[基础] HTTPEndpoint =>', ep);


// ============================================================
// 2. Uppercase / Lowercase / Capitalize / Uncapitalize
// ============================================================

type Upper = Uppercase<'hello'>;        // 'HELLO'
type Lower = Lowercase<'WORLD'>;        // 'world'
type Cap   = Capitalize<'foo'>;         // 'Foo'
type Uncap = Uncapitalize<'Bar'>;       // 'bar'

console.log('[大小写] =>',
  'HELLO' as Upper, '|',
  'world' as Lower, '|',
  'Foo' as Cap, '|',
  'bar' as Uncap);


// 在模板字面量里直接用这些内置工具
type Field = 'name' | 'age' | 'email';

type UpperField = Uppercase<Field>;     // 'NAME' | 'AGE' | 'EMAIL'
type ConstName = `CONFIG_${UpperField}`; // 'CONFIG_NAME' | 'CONFIG_AGE' | 'CONFIG_EMAIL'

const cn: ConstName = 'CONFIG_NAME';
console.log('[大小写+拼接] =>', cn);


// 把 snake_case 转 camelCase：Uncapitalize + 替换（示意）
// 注意：模板字面量本身不支持正则替换，需配合 infer 模式匹配
type SnakeToCamel<S extends string> =
  S extends `${infer Head}_${infer Tail}`
    ? `${Head}${Capitalize<SnakeToCamel<Tail>>}`
    : S;

type Camel1 = SnakeToCamel<'user_name'>;        // 'userName'
type Camel2 = SnakeToCamel<'user_id_card'>;     // 'userIdCard'
type Camel3 = SnakeToCamel<'simple'>;           // 'simple'
console.log('[大小写+infer] SnakeToCamel =>', 'userName' as Camel1, '|', 'userIdCard' as Camel2);


// ============================================================
// 3. 结合 keyof + as 生成 getter / setter 名
// ============================================================

interface User {
  id: number;
  name: string;
  email: string;
  isActive: boolean;
}

// 3.1 为每个字段生成 getter 方法签名
type Getters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};

type UserGetters = Getters<User>;
// { getId: () => number; getName: () => string; getEmail: () => string; getIsActive: () => boolean }

const ug: UserGetters = {
  getId:       () => 1,
  getName:     () => 'Alice',
  getEmail:    () => 'a@x.com',
  getIsActive: () => true,
};
console.log('[keyof+as Getters] =>',
  ug.getId(), ug.getName(), ug.getEmail(), ug.getIsActive());


// 3.2 为每个字段生成 setter 方法签名
type Setters<T> = {
  [K in keyof T as `set${Capitalize<string & K>}`]: (value: T[K]) => void;
};

type UserSetters = Setters<User>;
// { setId: (v: number) => void; setName: (v: string) => void; ... }

const us: UserSetters = {
  setId:       (v) => console.log('  setId', v),
  setName:     (v) => console.log('  setName', v),
  setEmail:    (v) => console.log('  setEmail', v),
  setIsActive: (v) => console.log('  setIsActive', v),
};
us.setId(2);
us.setName('Bob');


// 3.3 同时生成 getter + setter（用交叉类型合并）
type Accessors<T> = Getters<T> & Setters<T>;

type UserAccessors = Accessors<User>;
// 既有 getXxx 也有 setXxx

const ua: UserAccessors = {
  getId:       () => 3,
  getName:     () => 'Carol',
  getEmail:    () => 'c@x.com',
  getIsActive: () => false,
  setId:       (v) => console.log('  setId', v),
  setName:     (v) => console.log('  setName', v),
  setEmail:    (v) => console.log('  setEmail', v),
  setIsActive: (v) => console.log('  setIsActive', v),
};
console.log('[keyof+as Accessors] =>', ua.getId(), ua.getName());


// 3.4 实现一个真正可用的“强类型访问器工厂”
function makeAccessors<T extends object>(target: T): Accessors<T> {
  const result: any = {};
  (Object.keys(target) as Array<keyof T & string>).forEach((key) => {
    const capKey = key.charAt(0).toUpperCase() + key.slice(1);
    result[`get${capKey}`] = () => target[key];
    result[`set${capKey}`] = (v: any) => { (target as any)[key] = v; };
  });
  return result as Accessors<T>;
}

const userObj = { id: 1, name: 'Dave', email: 'd@x.com', isActive: true };
const accessor = makeAccessors(userObj);
console.log('[工厂 makeAccessors] before =>', accessor.getName());
accessor.setName('Dave II');
console.log('[工厂 makeAccessors] after  =>', accessor.getName());


// ============================================================
// 4. 实战模式
// ============================================================

// 4.1 路由表：以路径字面量作为键，类型安全
type Route = `/users` | `/users/${number}` | `/posts/${number}` | `/posts/${number}/comments`;

const r1: Route = '/users';
const r2: Route = '/users/123';
const r3: Route = '/posts/42/comments';
console.log('[路由表] =>', r1, '|', r2, '|', r3);


// 4.2 事件名：模块 + 动作
type Module = 'user' | 'article' | 'comment';
type Action = 'created' | 'updated' | 'deleted';
type EventName = `${Module}.${Action}`;
// 'user.created' | 'user.updated' | ... 共 9 种

function emit(event: EventName, payload: unknown) {
  console.log('  [emit]', event, '=>', JSON.stringify(payload));
}
emit('user.created', { id: 1 });
emit('article.updated', { id: 2 });
// emit('user.banned', {});   // ❌ 'banned' 不在 Action 中


// 4.3 CSS 类名生成
type Breakpoint = 'sm' | 'md' | 'lg';
type ColSpan = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12;
type ColClass = `col-${Breakpoint}-${ColSpan}`;
// 'col-sm-1' | 'col-sm-2' | ... | 'col-lg-12' 共 36 种

const cls: ColClass = 'col-md-6';
console.log('[CSS] ColClass =>', cls);


// 4.4 监听器类型：on + 事件名
type Listener<T> = {
  [K in keyof T & string as `on${Capitalize<K>}`]: (payload: T[K]) => void;
};

interface EventPayloads {
  open: { url: string };
  close: { reason: string };
  message: { text: string };
}

type WindowListeners = Listener<EventPayloads>;
// { onOpen: (p: { url: string }) => void; onClose: (p: { reason: string }) => void; onMessage: (p: { text: string }) => void }

const wl: WindowListeners = {
  onOpen:    (p) => console.log('  [onOpen]', p.url),
  onClose:   (p) => console.log('  [onClose]', p.reason),
  onMessage: (p) => console.log('  [onMessage]', p.text),
};
wl.onOpen({ url: 'https://ts.dev' });
wl.onClose({ reason: 'user' });
wl.onMessage({ text: 'hello' });


// 4.5 类型安全的 fetch 函数（路径 + 参数对应）
interface API {
  '/users/list': { query: { page: number }; response: { id: number; name: string }[] };
  '/users/create': { body: { name: string }; response: { id: number } };
  '/health': { response: { ok: boolean } };
}

type APIPath = keyof API;

type APIParams<P extends APIPath> =
  API[P] extends { query: infer Q; body: infer B }
    ? { query: Q; body: B }
    : API[P] extends { body: infer B }
      ? { body: B }
      : API[P] extends { query: infer Q }
        ? { query: Q }
        : {};

type APIResponse<P extends APIPath> = API[P] extends { response: infer R } ? R : never;

function api<P extends APIPath>(path: P, params: APIParams<P>): Promise<APIResponse<P>> {
  console.log('  [api]', path, JSON.stringify(params));
  return Promise.resolve({} as APIResponse<P>);
}

// 类型自动推断出 params 与返回值的形状
api('/users/list', { query: { page: 1 } }).then((r) => console.log('  [api resp]', r));
api('/users/create', { body: { name: 'Eve' } }).then((r) => console.log('  [api resp]', r));
api('/health', {}).then((r) => console.log('  [api resp]', r));
// api('/users/list', { body: { name: 'x' } });   // ❌ body 不在参数类型中


console.log('\n--- template-literal.ts 执行完毕 ---');
