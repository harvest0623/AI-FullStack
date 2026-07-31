/**
 * Day09 - 迷你路由装饰器（mini Controller）
 *
 * 用 @Controller(prefix) + @Get(path) + @Post(path) + @Param/@Body/@Query
 * 复刻 NestJS 控制器的最小内核：
 *   1. 类装饰器 @Controller 贴上路由前缀
 *   2. 方法装饰器 @Get/@Post 贴上 HTTP 方法与子路径
 *   3. 参数装饰器 @Param/@Body/@Query 标记参数从请求何处取
 *   4. 一个简单的 Router 注册表，启动时扫描所有 Controller，注册路由
 */

import 'reflect-metadata';

// ---------- 元数据 key ----------
const CONTROLLER_KEY = Symbol('http:controller');
const ROUTE_KEY = Symbol('http:route');
const PARAM_META = Symbol('http:param');

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';

type ParamAnnotation = {
  index: number;
  kind: 'param' | 'body' | 'query';
  name?: string;
};

// ---------- 类装饰器：Controller ----------
function Controller(prefix: string): ClassDecorator {
  return function (target: any) {
    Reflect.defineMetadata(CONTROLLER_KEY, prefix, target);
    return target;
  };
}

// ---------- 方法装饰器：Get / Post / Put / Delete ----------
function createRoute(method: HttpMethod, path: string): MethodDecorator {
  return function (target: any, propertyKey: string | symbol, descriptor: PropertyDescriptor) {
    Reflect.defineMetadata(
      ROUTE_KEY,
      { method, path },
      target,
      propertyKey,
    );
    return descriptor;
  };
}

function Get(path: string) { return createRoute('GET', path); }
function Post(path: string) { return createRoute('POST', path); }
function Put(path: string) { return createRoute('PUT', path); }
function Delete(path: string) { return createRoute('DELETE', path); }

// ---------- 参数装饰器：Param / Body / Query ----------
function addParam(
  target: any,
  propertyKey: string | symbol,
  index: number,
  annotation: Omit<ParamAnnotation, 'index'>,
) {
  const list: ParamAnnotation[] =
    Reflect.getOwnMetadata(PARAM_META, target, propertyKey) ?? [];
  list.push({ index, ...annotation });
  Reflect.defineMetadata(PARAM_META, list, target, propertyKey);
}

function Param(name: string): ParameterDecorator {
  return (t, pk, i) => addParam(t, pk as string, i, { kind: 'param', name });
}
function Body(target: any, propertyKey: string | symbol, index: number) {
  addParam(target, propertyKey, index, { kind: 'body' });
}
function Query(name: string): ParameterDecorator {
  return (t, pk, i) => addParam(t, pk as string, i, { kind: 'query', name });
}

// ---------- 路由表与启动器 ----------
type RouteEntry = {
  method: HttpMethod;
  fullpath: string;
  handler: (ctx: RequestContext) => any;
};

interface RequestContext {
  params: Record<string, string>;
  query: Record<string, string>;
  body: any;
}

class Router {
  private routes: RouteEntry[] = [];

  register(controller: object) {
    const proto = Object.getPrototypeOf(controller);
    const prefix: string = Reflect.getMetadata(CONTROLLER_KEY, controller.constructor) ?? '';
    const methods = Object.getOwnPropertyNames(proto).filter(
      (m) => m !== 'constructor' && typeof proto[m] === 'function',
    );

    for (const m of methods) {
      const routeMeta = Reflect.getMetadata(ROUTE_KEY, proto, m);
      if (!routeMeta) continue; // 没贴 @Get/@Post 的方法跳过

      const paramAnnos: ParamAnnotation[] =
        Reflect.getOwnMetadata(PARAM_META, proto, m) ?? [];

      const handler = (ctx: RequestContext) => {
        const maxIndex = paramAnnos.length ? Math.max(...paramAnnos.map((a) => a.index)) : -1;
        const args: any[] = new Array(maxIndex + 1);
        for (const a of paramAnnos) {
          if (a.kind === 'param') args[a.index] = ctx.params[a.name!];
          else if (a.kind === 'query') args[a.index] = ctx.query[a.name!];
          else if (a.kind === 'body') args[a.index] = ctx.body;
        }
        return (proto[m] as (...a: any[]) => any).apply(controller, args);
      };

      const fullpath = `${prefix}${routeMeta.path}`.replace(/\/+/g, '/');
      this.routes.push({ method: routeMeta.method, fullpath, handler });
      console.log(`[Router] 注册 ${routeMeta.method} ${fullpath}`);
    }
  }

  list() {
    return this.routes.map((r) => `${r.method} ${r.fullpath}`);
  }

  dispatch(method: string, fullpath: string, ctx: RequestContext): any {
    const route = this.routes.find(
      (r) => r.method === method && r.fullpath === fullpath,
    );
    if (!route) return { status: 404, body: 'Not Found' };
    return { status: 200, body: route.handler(ctx) };
  }
}

// ---------- 业务：定义控制器 ----------
@Controller('/users')
class UserController {
  @Get('/:id')
  findOne(@Param('id') id: string) {
    return { id: Number(id), name: 'Alice' };
  }

  @Get('')
  list(@Query('page') page: string) {
    return { page: Number(page) || 1, items: ['Alice', 'Bob'] };
  }

  @Post('')
  create(@Body body: { name: string; age: number }) {
    return { id: 100, ...body };
  }

  @Put('/:id')
  update(@Param('id') id: string, @Body body: { name: string }) {
    return { id: Number(id), ...body };
  }

  @Delete('/:id')
  remove(@Param('id') id: string) {
    return { deleted: Number(id) };
  }
}

// ---------- 启动 ----------
const router = new Router();
router.register(new UserController());

console.log('\n路由表：');
console.log(router.list());

console.log('\n模拟请求：');
console.log(router.dispatch('GET', '/users/42', { params: { id: '42' }, query: {}, body: null }));
console.log(router.dispatch('GET', '/users', { params: {}, query: { page: '2' }, body: null }));
console.log(router.dispatch('POST', '/users', { params: {}, query: {}, body: { name: 'Bob', age: 30 } }));
console.log(router.dispatch('PUT', '/users/1', { params: { id: '1' }, query: {}, body: { name: 'Bob2' } }));
console.log(router.dispatch('DELETE', '/users/9', { params: { id: '9' }, query: {}, body: null }));
console.log(router.dispatch('GET', '/not-exist', { params: {}, query: {}, body: null }));

console.log('\n[mini-controller.ts] 运行结束');
