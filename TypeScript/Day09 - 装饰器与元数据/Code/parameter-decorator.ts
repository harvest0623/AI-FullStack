/**
 * Day09 - 参数装饰器（ParameterDecorator）
 *
 * 签名：(target, propertyKey, parameterIndex: number) => void
 * - target：静态方法参数时为构造函数；实例方法参数时为原型对象
 * - propertyKey：方法名（普通函数参数 / 构造函数参数 时为 undefined）
 * - parameterIndex：参数在形参列表中的下标
 * - 返回值被忽略
 *
 * 参数装饰器本身不能改变参数行为，只能"在某个方法的第 N 个参数上贴标签"，
 * 由方法装饰器或框架在运行时读取这些标签做出动作（NestJS 的 @Body/@Query/@Param 正是这个套路）。
 */

import 'reflect-metadata';

// ---------- 1. 最基础：记录参数索引 ----------
function Mark(target: any, propertyKey: string, parameterIndex: number) {
  console.log(`[Mark] ${propertyKey ?? '<构造函数>'} 的第 ${parameterIndex} 个参数被标记`);
}

class OrderService {
  create(@Mark name: string, @Mark qty: number) {
    return { name, qty };
  }
}

// ---------- 2. NestJS 风格的 @Param / @Body / @Query ----------
const PARAM_META = 'method:param-annotations';

type ParamAnnotation = { index: number; kind: 'param' | 'body' | 'query'; name?: string };

function addParamAnnotation(
  target: any,
  propertyKey: string | symbol,
  parameterIndex: number,
  annotation: Omit<ParamAnnotation, 'index'>,
) {
  const list: ParamAnnotation[] =
    Reflect.getOwnMetadata(PARAM_META, target, propertyKey) ?? [];
  list.push({ index: parameterIndex, ...annotation });
  Reflect.defineMetadata(PARAM_META, list, target, propertyKey);
}

function Param(name: string) {
  return (target: any, propertyKey: string, parameterIndex: number) => {
    addParamAnnotation(target, propertyKey, parameterIndex, { kind: 'param', name });
  };
}

function Body(target: any, propertyKey: string, parameterIndex: number) {
  addParamAnnotation(target, propertyKey, parameterIndex, { kind: 'body' });
}

function Query(name: string) {
  return (target: any, propertyKey: string, parameterIndex: number) => {
    addParamAnnotation(target, propertyKey, parameterIndex, { kind: 'query', name });
  };
}

// 用一个方法装饰器读取参数注解，演示"参数装饰器 + 方法装饰器"协作
function Route(method: string, path: string) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const annotations: ParamAnnotation[] =
      Reflect.getOwnMetadata(PARAM_META, target, propertyKey) ?? [];
    const original = descriptor.value;

    descriptor.value = function (this: any, ctx: {
      params: Record<string, string>;
      query: Record<string, string>;
      body: any;
    }) {
      const args = new Array(annotations.length ? Math.max(...annotations.map((a) => a.index)) + 1 : 0);
      for (const a of annotations) {
        if (a.kind === 'param') args[a.index] = ctx.params[a.name!];
        else if (a.kind === 'query') args[a.index] = ctx.query[a.name!];
        else if (a.kind === 'body') args[a.index] = ctx.body;
      }
      return original.apply(this, args);
    };

    console.log(`[Route] 注册 ${method.toUpperCase()} ${path} → ${propertyKey}()`);
  };
}

class UserController {
  @Route('GET', '/users/:id')
  getUser(@Param('id') id: string) {
    return { id, name: 'Alice' };
  }

  @Route('POST', '/users')
  createUser(@Body body: { name: string }) {
    return { id: 'new', ...body };
  }

  @Route('GET', '/users')
  listUsers(@Query('page') page: string) {
    return { page: Number(page), items: [] };
  }
}

const ctrl = new UserController();
console.log(ctrl.getUser({ params: { id: '42' }, query: {}, body: null }));
console.log(ctrl.createUser({ params: {}, query: {}, body: { name: 'Bob' } }));
console.log(ctrl.listUsers({ params: {}, query: { page: '2' }, body: null }));

// ---------- 3. 构造函数参数装饰器（NestJS @Inject） ----------
const INJECT_KEY = 'constructor:inject-tokens';

function Inject(token: string) {
  return function (target: any, propertyKey: undefined, parameterIndex: number) {
    // 构造函数参数：propertyKey 为 undefined
    const list: Record<number, string> =
      Reflect.getOwnMetadata(INJECT_KEY, target) ?? {};
    list[parameterIndex] = token;
    Reflect.defineMetadata(INJECT_KEY, list, target);
  };
}

class LoggerService {}
class CacheService {}

class AppService {
  constructor(
    @Inject('Logger') private logger: LoggerService,
    @Inject('Cache') private cache: CacheService,
  ) {}
}

console.log(Reflect.getOwnMetadata(INJECT_KEY, AppService));
// { '0': 'Logger', '1': 'Cache' } —— 这正是 NestJS 容器装配时读取的元数据

console.log('\n[parameter-decorator.ts] 运行结束');
