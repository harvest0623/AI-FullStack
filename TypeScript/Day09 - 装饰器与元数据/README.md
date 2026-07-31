# Day09 - 装饰器与元数据

> 本篇聚焦 TypeScript 中最具“元编程”色彩的能力——**装饰器（Decorator）**与**元数据反射（Reflect Metadata）**。装饰器让你能在不修改原有类/方法/属性源码的前提下，以“贴标签”的方式叠加日志、权限、缓存、路由、依赖注入等横切逻辑；元数据反射则让运行时代码“看见”编译期的类型信息。**装饰器是 NestJS 的核心机制——理解装饰器，就理解了 NestJS 的一半**。掌握本篇后，你将拥有从 TypeScript 语法层平滑进入 NestJS 工程实践的全部前置知识。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解 - 装饰器是什么](#二理论知识讲解---装饰器是什么)
  - [2.1 从 AOP 与装饰器模式说起](#21-从-aop-与装饰器模式说起)
  - [2.2 注解 annotation：贴在代码上的“标签”](#22-注解-annotation贴在代码上的标签)
  - [2.3 TS 装饰器的历史与现状](#23-ts-装饰器的历史与现状)
  - [2.4 开启装饰器：experimentalDecorators 与 emitDecoratorMetadata](#24-开启装饰器-experimentaldecorators-与-emitdecoratormetadata)
- [三、四种装饰器签名](#三四种装饰器签名)
- [四、装饰器工厂](#四装饰器工厂)
- [五、装饰器执行顺序](#五装饰器执行顺序)
- [六、reflect-metadata 与元数据反射](#六-reflect-metadata-与元数据反射)
  - [6.1 元数据反射的基本 API](#61-元数据反射的基本-api)
  - [6.2 设计时类型信息：design:type / design:paramtypes / design:returntype](#62-设计时类型信息-designtype--designparamtypes--designreturntype)
  - [6.3 emitDecoratorMetadata 的作用](#63-emitdecoratormetadata-的作用)
- [七、四种装饰器详解与代码示例](#七四种装饰器详解与代码示例)
  - [7.1 类装饰器 ClassDecorator](#71-类装饰器-classdecorator)
  - [7.2 方法装饰器 MethodDecorator](#72-方法装饰器-methoddecorator)
  - [7.3 属性装饰器 PropertyDecorator](#73-属性装饰器-propertydecorator)
  - [7.4 参数装饰器 ParameterDecorator](#74-参数装饰器-parameterdecorator)
- [八、装饰器实战](#八装饰器实战)
  - [8.1 @Log 方法日志装饰器](#81-log-方法日志装饰器)
  - [8.2 @Deprecated 标记弃用](#82-deprecated-标记弃用)
  - [8.3 @RequireRole 权限校验（为 NestJS Guard 铺垫）](#83-requirerole-权限校验为-nestjs-guard-铺垫)
  - [8.4 @Inject 依赖注入标记（迷你 DI 容器演示）](#84-inject-依赖注入标记迷你-di-容器演示)
  - [8.5 @Controller/@Get/@Post 路由装饰器迷你实现（为 NestJS 控制器铺垫）](#85-controllergetpost-路由装饰器迷你实现为-nestjs-控制器铺垫)
- [九、装饰器与 NestJS 的关系](#九装饰器与-nestjs-的关系)
- [十、关键知识点总结](#十关键知识点总结)
- [十一、实战练习](#十一实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 准确说出 AOP、装饰器模式、注解三者的关系，以及 TS 装饰器在三者中扮演的角色。
2. 描述 TS 装饰器从 stage 1 实验性到 TC39 stage 3 的演进，以及 TS 5.0 引入的新装饰器语法与旧实验性装饰器的关键差异。
3. 配置 `experimentalDecorators` 与 `emitDecoratorMetadata`，并解释二者各自的职责。
4. 写出四种装饰器（类 / 方法 / 属性 / 参数）的签名，解释每个参数的含义。
5. 用装饰器工厂实现“可传参”的装饰器，并解释工厂函数与真正装饰器的关系。
6. 复述多种装饰器同时存在时的执行顺序（实例优先于静态、属性优先于方法、参数先于方法、类装饰器最后、同位置多个装饰器工厂按书写顺序求值、本体从下到上执行）。
7. 用 `reflect-metadata` 的 `defineMetadata` / `getMetadata` 自定义元数据，并解读 `design:type` / `design:paramtypes` / `design:returntype` 三类设计时类型信息。
8. 实现迷你 DI 容器（`@Injectable` + `@Inject`），依赖构造函数参数元数据完成自动装配。
9. 实现迷你路由装饰器（`@Controller` + `@Get` + `@Post`），理解 NestJS 控制器的底层模型。
10. 在阅读 NestJS 源码或业务代码时，能立刻识别每一条装饰器的作用位置与作用机制。

---

## 二、理论知识讲解 - 装饰器是什么

### 2.1 从 AOP 与装饰器模式说起

**AOP（Aspect-Oriented Programming，面向切面编程）** 的核心思想是：把那些“横切”在多个业务方法上的关注点（日志、权限、事务、缓存、链路追踪）从业务代码中抽离出来，集中表达，再在合适的时机“织入”到目标方法。这样，业务方法只关心业务本身，而横切逻辑被复用、统一管理。

在 Java Spring 里，AOP 通过动态代理 + 字节码织入实现；在 TS/JS 里，装饰器是表达 AOP 的最自然语法——你在方法上“贴一个标签”，这个标签背后可以包一层切面逻辑：

```ts
function Log(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
  const original = descriptor.value;
  descriptor.value = function (...args: any[]) {
    console.log(`[Log] 调用 ${propertyKey}`);
    return original.apply(this, args);
  };
}

class OrderService {
  @Log
  cancel(id: number) { /* ... */ }
}
```

**装饰器模式（Decorator Pattern）** 是 GoF 23 种设计模式之一：在不改变原对象的前提下，通过“包装”的方式给对象增加新行为。从结构上看，TS 类装饰器正是装饰器模式的语法糖——它接收一个构造函数，返回一个被增强的（通常是继承自原类的）新构造函数：

```ts
function Timestamped<T extends new (...args: any[]) => any>(Base: T) {
  return class extends Base {
    createdAt = new Date();
  };
}
```

### 2.2 注解 annotation：贴在代码上的“标签”

**注解（Annotation）** 的语义是“贴标签”：你给一段代码附加一个标记，这个标记本身可能不做任何事，只是被其它工具（编译器、运行时框架、代码生成器）读取并赋予意义。Java 的 `@Override`、`@Autowired`，Python 的 `@dataclass`，都是注解。

TS 装饰器兼具两种身份：

- **作为 AOP 切面**：在装饰器函数里写“前置 / 后置 / 包装”逻辑，运行时改变行为（常见于日志、权限、缓存）。
- **作为注解**：在装饰器里只往元数据上写信息，**什么都不做**（常见于 `@Controller`、`@Get('/users')`、`@Injectable()`），由框架在启动时扫描这些元数据再驱动行为。

NestJS 大量装饰器属于后者——它们本身不改变类的行为，只是“贴标签”，由 NestJS 的扫描器与容器读取标签后决定路由、注入、守卫、拦截器等。这一点至关重要：**很多 NestJS 装饰器看起来“魔法十足”，本质只是一个 `Reflect.defineMetadata` 调用**。

### 2.3 TS 装饰器的历史与现状

TS 装饰器的演进有三条时间线需要分清：

| 阶段 | 时间 | 规范 | TS 支持 |
|------|------|------|---------|
| Stage 1 装饰器（实验性） | 2015 | ES 草案 stage 1 | TS 1.5+ 通过 `experimentalDecorators` 开启 |
| Stage 2 装饰器 | 2018–2022 | TC39 推进至 stage 2 | 期间多次讨论但未默认开启 |
| Stage 3 装饰器（标准） | 2023 | TC39 推进至 stage 3 | TS 5.0 原生支持（无需 `experimentalDecorators`） |

**TS 5.0 引入的 stage 3 装饰器**与旧的实验性装饰器有几个关键差异：

1. **不需要 `experimentalDecorators`**：开箱即用。
2. **不与 `emitDecoratorMetadata` 联动**：stage 3 装饰器无法直接拿到 `design:paramtypes`，这是 NestJS 暂时仍使用旧装饰器的主要原因。
3. **API 形态不同**：stage 3 装饰器接收一个 context 对象（`{ kind, name, addInitializer }`），返回值是新值（被替换的类 / 方法），而不是直接接收 constructor / descriptor。
4. **不能装饰参数**：stage 3 当前不支持参数装饰器（NestJS 大量使用 `@Inject()` `@Body()` 等参数装饰器，这是另一阻碍）。

由于 NestJS 强依赖 `emitDecoratorMetadata` + 参数装饰器，目前生产中绝大多数 NestJS 项目仍使用 **旧实验性装饰器**（`experimentalDecorators: true`）。本篇所有代码也基于旧实验性装饰器编写，这也是 NestJS 5.x / 10.x 的实际运行形态。stage 3 装饰器更适合纯 TS 工具链、lit 等不依赖元数据的场景，可作为延伸阅读了解。

### 2.4 开启装饰器：experimentalDecorators 与 emitDecoratorMetadata

`tsconfig.json` 中两个关键开关：

```json
{
  "compilerOptions": {
    "experimentalDecorators": true,
    "emitDecoratorMetadata": true
  }
}
```

- **`experimentalDecorators: true`**：告诉 TS 编译器“允许使用旧实验性装饰器语法”，并在编译产物里生成对应的 `__decorate`、`__metadata` 辅助调用。
- **`emitDecoratorMetadata: true`**：在生成 `__decorate` 调用时，额外插入 `__metadata("design:type", ...)` 等元数据注入语句，把编译期可见的类型信息（`Function`、`String`、`Number`、构造函数引用等）写到运行时。这一开关只有在 `experimentalDecorators` 打开时才生效。

> ⚠️ 没有 `emitDecoratorMetadata`，NestJS 的 `constructor(private users: UsersService)` 这种“构造函数自动注入”就会失效——因为运行时拿不到 `UsersService` 这个构造函数引用，无法完成装配。

---

## 三、四种装饰器签名

旧实验性装饰器共有四种位置，签名各不相同：

| 位置 | 签名 | 返回值 |
|------|------|--------|
| 类 | `(constructor: T) => T \| void` | 新构造函数或 void |
| 方法 | `(target, propertyKey, descriptor: TypedPropertyDescriptor<T>) => TypedPropertyDescriptor<T> \| void` | 新描述符或 void |
| 属性 | `(target, propertyKey) => void` | （忽略） |
| 参数 | `(target, propertyKey, parameterIndex: number) => void` | （忽略） |

**类装饰器**

```ts
type ClassDecorator = <TFunction extends Function>(
  target: TFunction
) => TFunction | void;
```

`target` 是被装饰类的构造函数本身。返回新构造函数会用它替换原类；返回 `void` 则保留原类。

**方法装饰器**

```ts
type MethodDecorator = <T>(
  target: Object,
  propertyKey: string | symbol,
  descriptor: TypedPropertyDescriptor<T>
) => TypedPropertyDescriptor<T> | void;
```

- `target`：静态方法装饰器拿到的是类的构造函数，实例方法装饰器拿到的是原型对象（`Class.prototype`）。
- `descriptor.value` 就是方法本身，改写它即完成“方法包装”。
- 返回新描述符会替换原描述符。

**属性装饰器**

```ts
type PropertyDecorator = (target: Object, propertyKey: string | symbol) => void;
```

注意：属性装饰器**没有 descriptor**（TS 编译属性时不会为每个实例字段生成描述符，只用 `[[Define]]` 语义赋值）。若想拿到属性类型，必须配合 `reflect-metadata` 读取 `design:type`。

**参数装饰器**

```ts
type ParameterDecorator = (
  target: Object,
  propertyKey: string | symbol | undefined,   // 构造函数参数时为 undefined
  parameterIndex: number
) => void;
```

参数装饰器返回值被忽略，唯一作用是“在某个方法的第 N 个参数上贴个标签”，元数据通过 `reflect-metadata` 写入。

---

## 四、装饰器工厂

直接写 `@Log` 时，`Log` 本身就是装饰器函数。但很多时候我们希望装饰器能接收参数（`@RequireRole('admin')`、`@Get('/users')`）——这时就要写成**装饰器工厂**：

```ts
function RequireRole(role: string) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const original = descriptor.value;
    descriptor.value = function (...args: any[]) {
      console.log(`[权限] 当前需要角色：${role}`);
      return original.apply(this, args);
    };
  };
}

class OrderService {
  @RequireRole('admin')
  deleteOrder(id: number) { /* ... */ }
}
```

工厂的关键点：

1. **工厂本身不是装饰器**，它只是被 `()` 调用一次，返回的函数才是装饰器。
2. **执行时机**：工厂函数在类定义时立即执行，返回的装饰器随后立即执行。
3. **传参方式**：`@Factory(args)` 等价于先 `Factory(args)` 拿到装饰器，再把它贴上去。
4. **多装饰器工厂并存时**：工厂按书写顺序（自上而下）求值，但装饰器本体按自下而上执行（洋葱模型），详见下一节。

---

## 五、装饰器执行顺序

当多种装饰器并存时，执行顺序遵循以下规则（TS 官方手册明文规定）：

1. **实例成员优先于静态成员**：先执行所有实例上的装饰器，再执行静态上的。
2. **属性优先于方法**：同一类上，属性装饰器先于方法装饰器执行。
3. **参数装饰器先于方法装饰器**：方法上的参数装饰器在所属方法装饰器**之前**执行。
4. **类装饰器最后**：类装饰器在所有成员装饰器都执行完之后才执行。
5. **同位置多个装饰器**：工厂按书写顺序求值，装饰器本体**从下到上**执行（洋葱模型）。

完整顺序：

```
1. 实例属性装饰器（按出现顺序）
2. 实例方法装饰器（参数装饰器先于方法装饰器）
3. 静态属性装饰器
4. 静态方法装饰器（参数装饰器先于方法装饰器）
5. 构造函数参数装饰器
6. 类装饰器（从下到上）
```

记忆口诀：**“实例 → 静态 → 构造参数 → 类”，每层内部“参数 → 属性 → 方法”，同位置多个装饰器“工厂按顺序、本体从下到上”**。

示例验证（见 `Code/decorator-factory.ts`）：

```ts
class Demo {
  @A('top')
  @B('bottom')
  hello() {}
}
// 输出顺序：
//   工厂 A(top) 求值
//   工厂 B(bottom) 求值
//   装饰器 B(bottom) 执行
//   装饰器 A(top) 执行
```

---

## 六、reflect-metadata 与元数据反射

### 6.1 元数据反射的基本 API

[`reflect-metadata`](https://www.npmjs.com/package/reflect-metadata) 是一个 polyfill，它把 ES Reflect 对象扩展出一组元数据 API，允许你在任意对象 / 属性上“贴”任意键值对。类型声明随 `reflect-metadata` 包自带（`@types/reflect-metadata` 实际已合并入主包，只需 `import 'reflect-metadata'` 即可）。

```ts
import 'reflect-metadata';

const META_KEY = 'custom:role';

function Role(role: string) {
  return (target: any, propertyKey: string) => {
    Reflect.defineMetadata(META_KEY, role, target, propertyKey);
  };
}

class AdminPanel {
  @Role('admin')
  reboot() {}
}

console.log(Reflect.getMetadata(META_KEY, AdminPanel.prototype, 'reboot')); // 'admin'
```

关键 API：

| API | 作用 |
|-----|------|
| `Reflect.defineMetadata(key, value, target, propertyKey?)` | 在 target（或 target 的某属性）上写入元数据 |
| `Reflect.getMetadata(key, target, propertyKey?)` | 读取元数据（会沿原型链向上查找） |
| `Reflect.getOwnMetadata(key, target, propertyKey?)` | 读取自身元数据（不沿原型链） |
| `Reflect.hasMetadata / hasOwnMetadata` | 是否存在某元数据 |
| `Reflect.getMetadataKeys / getOwnMetadataKeys` | 列出所有元数据 key |

工程化建议：把所有 metadata key 集中到一个常量对象里管理（NestJS 内部源码就是这么做的），避免散落魔法字符串：

```ts
const META_KEYS = {
  injectable: Symbol('di:injectable'),
  inject: Symbol('di:inject'),
  route: Symbol('http:route'),
} as const;
```

### 6.2 设计时类型信息：design:type / design:paramtypes / design:returntype

`emitDecoratorMetadata: true` 会让 TS 在被装饰的位置自动注入三类“设计时类型信息”，使用三个固定 key：

| Key | 注入位置 | 内容 |
|-----|---------|------|
| `design:type` | 被装饰的属性 / 方法 | 属性的类型（构造函数）/ 方法的 `Function` |
| `design:paramtypes` | 被装饰的方法 / 类 | 形参类型数组（构造函数数组） |
| `design:returntype` | 被装饰的方法 | 返回值类型（构造函数） |

这些 key 必须通过 `Reflect.getMetadata('design:paramtypes', ...)` 读取，且**只有在该位置存在装饰器时才会被注入**——未装饰的方法 / 属性 / 类不会自动产生这些元数据。

注意事项：

- `design:type` 在遇到 `number | string` 这类联合类型时只能拿到 `Object`，因为运行时无法表达“或”。
- 接口类型（如 `IConfig`）在运行时拿不到，只能拿到 `Object`——这正是 NestJS 中“接口抽象必须配 token + `@Inject(token)`”的原因。
- `Promise<T>` 的 `design:returntype` 是 `Promise`，不会保留泛型参数 `T`。

### 6.3 emitDecoratorMetadata 的作用

`emitDecoratorMetadata` 是 NestJS 依赖注入的命脉。NestJS 通过它读取控制器 / Provider 构造函数的 `design:paramtypes`，从而知道“要给这个控制器注入哪些依赖”，再递归解析每个依赖：

```ts
@Injectable()
class UsersController {
  constructor(
    private readonly usersService: UsersService,    // ← design:paramtypes: [UsersService]
    private readonly logger: LoggerService,         // ← 也出现在 paramtypes 数组中
  ) {}
}
```

没有 `emitDecoratorMetadata`，NestJS 的 `constructor(private x: XService)` 自动注入就不可能成立——这是为什么 NestJS 至今仍坚守旧实验性装饰器的根本原因。

---

## 七、四种装饰器详解与代码示例

### 7.1 类装饰器 ClassDecorator

类装饰器签名 `(constructor: T) => T | void`，两种典型用法：

```ts
// 用法 1：直接修改原型（不返回值）
function ApiClass(target: Function) {
  target.prototype.endpoint = '/api';
}

// 用法 2：返回继承自原类的新构造函数
function Timestamped<T extends new (...args: any[]) => any>(Base: T) {
  return class extends Base {
    createdAt = new Date();
  };
}
```

详见 `Code/class-decorator.ts`，覆盖：原型扩展、返回新构造函数、`@Sealed` + `@Logged` 组合、纯元数据贴标签（`@Controller` 雏形）。

### 7.2 方法装饰器 MethodDecorator

方法装饰器签名 `(target, propertyKey, descriptor) => ...`，三种典型用法：

```ts
// 1. 修改 descriptor.value 做切面
function Log(target: any, key: string, d: PropertyDescriptor) {
  const original = d.value;
  d.value = function (...args: any[]) {
    console.log(`[Log] ${key}`);
    return original.apply(this, args);
  };
}

// 2. 修改 descriptor.writable 把方法只读化
function ReadOnly(target: any, key: string, d: PropertyDescriptor) {
  d.writable = false;
}

// 3. 返回新 descriptor 替换原描述符
function Once(target: any, key: string, d: PropertyDescriptor) {
  const original = d.value;
  const cache = new WeakMap();
  return {
    ...d,
    value: function (this: any, ...args: any[]) {
      if (cache.has(this)) return cache.get(this);
      const r = original.apply(this, args);
      cache.set(this, r);
      return r;
    },
  };
}
```

详见 `Code/method-decorator.ts`，覆盖 `@Log` 切面（同步 + 异步）、`@ReadOnly`、`@Once` 返回新描述符、静态方法 vs 实例方法的 `target` 差异。

### 7.3 属性装饰器 PropertyDecorator

属性装饰器签名 `(target, propertyKey) => void`，没有 descriptor。核心用法是“贴标签 + 配合 reflect-metadata 读取 `design:type`”：

```ts
import 'reflect-metadata';

function TypeLog(target: any, propertyKey: string) {
  const t = Reflect.getMetadata('design:type', target, propertyKey);
  console.log(`${propertyKey} 的类型是 ${t?.name}`);
}

class UserDTO {
  @TypeLog id: number;
  @TypeLog name: string;
  @TypeLog birthday: Date;
}
```

详见 `Code/property-decorator.ts`，覆盖 `@TypeLog` 读取 `design:type`、`@Required` 校验标签、`@Trim` 通过 `Object.defineProperty` 反向植入 getter/setter。

### 7.4 参数装饰器 ParameterDecorator

参数装饰器签名 `(target, propertyKey, parameterIndex) => void`，返回值被忽略。只能“贴标签”，由方法装饰器或框架读取：

```ts
const PARAM_META = Symbol('http:param');

function Param(name: string) {
  return (target: any, propertyKey: string, parameterIndex: number) => {
    const list = Reflect.getOwnMetadata(PARAM_META, target, propertyKey) ?? [];
    list.push({ index: parameterIndex, kind: 'param', name });
    Reflect.defineMetadata(PARAM_META, list, target, propertyKey);
  };
}

class UserController {
  findOne(@Param('id') id: string) { /* ... */ }
}
```

详见 `Code/parameter-decorator.ts`，覆盖基础索引标记、NestJS 风格 `@Param/@Body/@Query` + 方法装饰器协作、构造函数参数装饰器（`@Inject`）。

---

## 八、装饰器实战

### 8.1 @Log 方法日志装饰器

最经典的方法装饰器用例：包装 `descriptor.value`，在前后插入日志，并测量耗时。

```ts
function Log(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
  const original = descriptor.value;
  descriptor.value = function (...args: any[]) {
    console.log(`[Log] 调用 ${propertyKey}，参数：${JSON.stringify(args)}`);
    const start = Date.now();
    const result = original.apply(this, args);
    console.log(`[Log] ${propertyKey} 耗时 ${Date.now() - start}ms`);
    return result;
  };
}
```

> 对 `async` 方法的包装要小心：`original.apply` 返回的是 Promise，应改用 `async/await` 包装以正确捕获 `rejected`。详见 `Code/method-decorator.ts` 的 `@Log` 实现。

### 8.2 @Deprecated 标记弃用

```ts
function Deprecated(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
  const original = descriptor.value;
  descriptor.value = function (...args: any[]) {
    console.warn(`[Deprecated] ${propertyKey} 已弃用，请尽快迁移`);
    return original.apply(this, args);
  };
}

class LegacyAPI {
  @Deprecated
  oldFn() { /* ... */ }
}
```

### 8.3 @RequireRole 权限校验（为 NestJS Guard 铺垫）

工厂装饰器，把所需角色作为参数。这是 NestJS Guard 的最小内核——Guard 是更通用的“可注入 + 反射 + 路由元数据”形态，但底层机制完全一致：

```ts
function RequireRole(role: string) {
  return (target: any, propertyKey: string, descriptor: PropertyDescriptor) => {
    // 真实场景：贴元数据，由 Guard 读取
    Reflect.defineMetadata('role:required', role, target, propertyKey);
    // 演示用：直接在装饰器内做校验
    const original = descriptor.value;
    descriptor.value = function (this: any, user: { role: string }, ...rest: any[]) {
      if (user.role !== role) throw new Error(`需要 ${role} 角色`);
      return original.apply(this, rest);
    };
  };
}
```

### 8.4 @Inject 依赖注入标记（迷你 DI 容器演示）

完整实现见 `Code/mini-di-container.ts`，核心思路：

1. `@Injectable()` 给类贴“可被容器管理”标签。
2. `@Inject(token)` 给构造函数某参数贴“用此 token 解析”标签。
3. `Container.resolve(token)` 时，读取 `design:paramtypes` 拿到构造函数形参类型，再用 `@Inject` 元数据覆盖，递归解析依赖，最后 `new` 出实例并缓存（单例）。

```ts
@Injectable()
class UserService {
  constructor(
    private db: DatabaseService,                   // 靠 design:paramtypes 自动推断
    @Inject('IConfig') private config: IConfig,    // 接口类型拿不到，用 token 显式指定
  ) {}
}
```

这正是 NestJS Provider 系统的最小内核。

### 8.5 @Controller/@Get/@Post 路由装饰器迷你实现（为 NestJS 控制器铺垫）

完整实现见 `Code/mini-controller.ts`，核心思路：

1. `@Controller(prefix)` 类装饰器，把路由前缀贴到类上。
2. `@Get/@Post/@Put/@Delete(path)` 方法装饰器，把 HTTP 方法与子路径贴到方法上。
3. `@Param/@Body/@Query` 参数装饰器，标记每个参数从请求的何处取。
4. `Router.register(controller)` 启动时扫描所有方法元数据，组装成路由表。
5. `Router.dispatch(method, path, ctx)` 模拟请求分发。

这就是 NestJS 路由系统的“去魔法”版本——NestJS 在底层用的是 Express/Fastify + 一组元数据扫描器，但本质完全一致。

---

## 九、装饰器与 NestJS 的关系

把上面所有点拼起来，你会发现 NestJS 其实并不“魔法”：

| NestJS 概念 | 装饰器机制 | 本质 |
|-------------|-----------|------|
| `@Module()` | 类装饰器 + 元数据 | 贴标签：记录该模块的 controllers / providers / imports |
| `@Controller('/users')` | 类装饰器 + 元数据 | 贴标签：记录路由前缀 |
| `@Get('/:id')` | 方法装饰器 + 元数据 | 贴标签：记录 HTTP 方法与子路径 |
| `@Param/@Body/@Query` | 参数装饰器 + 元数据 | 贴标签：记录参数从请求何处取 |
| `@Injectable()` | 类装饰器 + 元数据 | 贴标签：标记该类可被容器管理 |
| `@Inject(token)` | 参数装饰器 + 元数据 | 贴标签：指定该参数用哪个 token 解析 |
| 构造函数自动注入 | `design:paramtypes` | `emitDecoratorMetadata` 让运行时拿到构造函数形参类型 |
| `@Guard()` / `@UseGuards()` | 方法装饰器 + 元数据 | 贴标签：标记该方法需要的权限 / 守卫 |
| `@Interceptor()` / `@Pipe()` | 同上 | 贴标签 + 框架在调用链中织入 |

一句话总结：**NestJS = 装饰器贴标签 + 容器 / 路由器 / 调用链读取标签 + Express/Fastify 跑 HTTP**。理解了装饰器与 reflect-metadata，NestJS 只是套了一层壳——后面进入 NestJS 时，你会看到 `@Controller` `@Get` `@Injectable` 这些“新东西”，但它们的内部机制你已经在这一章亲手实现过了。

---

## 十、关键知识点总结

1. **AOP**：把横切关注点（日志 / 权限 / 缓存 / 事务）从业务代码抽离，集中表达，统一织入；TS 装饰器是 AOP 在 TS/JS 中最自然的语法。
2. **装饰器模式**：GoF 设计模式之一，包装对象增加行为；TS 类装饰器返回继承子类正是其语法糖。
3. **注解语义**：很多 NestJS 装饰器本身不做行为，只 `Reflect.defineMetadata` 贴标签，由框架扫描驱动。
4. **TS 装饰器三阶段**：stage 1 实验性（`experimentalDecorators`）、stage 2、stage 3（TS 5.0 原生）。NestJS 因依赖 `emitDecoratorMetadata` 与参数装饰器，仍使用旧实验性装饰器。
5. **两个关键开关**：`experimentalDecorators` 开启语法；`emitDecoratorMetadata` 注入 `design:*` 元数据；后者依赖前者。
6. **四种装饰器签名**：类 `(ctor) => ctor | void`、方法 `(target, key, descriptor) => descriptor | void`、属性 `(target, key) => void`、参数 `(target, key?, index) => void`。
7. **属性装饰器无 descriptor**：要拿类型必须配合 `Reflect.getMetadata('design:type', ...)`。
8. **装饰器工厂**：`(...args) => Decorator`，工厂本身不是装饰器；多装饰器时工厂按书写顺序求值、本体从下到上执行。
9. **执行顺序**：实例 → 静态 → 构造参数 → 类；每层内部“参数 → 属性 → 方法”；同位置多装饰器“工厂按顺序、本体从下到上”。
10. **reflect-metadata**：`defineMetadata` / `getMetadata` / `getOwnMetadata`；`getMetadata` 沿原型链查找，`getOwnMetadata` 不查。
11. **设计时类型信息**：`design:type`（属性 / 方法）、`design:paramtypes`（方法 / 类）、`design:returntype`（方法）；只有被装饰的位置才会注入。
12. **联合类型 / 接口类型的退化**：`number | string` 退化为 `Object`，接口类型也拿不到，因此 NestJS 中“接口抽象必须配 token + `@Inject(token)`”。
13. **NestJS DI 命脉**：`emitDecoratorMetadata` 让 NestJS 能读到构造函数 `design:paramtypes`，从而自动装配依赖；没有它，`constructor(private x: XService)` 就不可能。
14. **NestJS 控制器模型**：`@Controller` 贴前缀，`@Get/@Post` 贴方法路径，`@Param/@Body/@Query` 贴参数来源，启动时扫描元数据组装路由表。
15. **去魔法视角**：NestJS = 装饰器贴标签 + 容器 / 路由器 / 调用链读标签 + Express/Fastify 跑 HTTP；理解了装饰器，NestJS 只是套壳。

---

## 十一、实战练习

> 以下练习配套 `Code/` 目录下的示例文件，建议先自己写，再对照参考实现。

### 练习 1：实现 `@Retry(n)` 方法装饰器（对应 `method-decorator.ts`）

写一个工厂装饰器 `@Retry(n)`，让被装饰的异步方法在抛错时自动重试最多 `n` 次，仍失败则抛出最后一次错误。要求：

1. 用 `async/await` 包装 `descriptor.value`，正确处理 Promise rejection。
2. 在每次重试前打印 `[Retry] 第 k 次重试`。
3. 写一个会随机失败（`Math.random() < 0.5` 抛错）的方法，验证 `@Retry(5)` 最终能成功。

**进阶**：把重试间隔做成指数退避（`100ms * 2^k`），并思考如何让重试只对特定错误类型生效（提示：用 `@Retry({ times: 5, on: NetworkError })` 工厂参数）。

### 练习 2：迷你校验框架（对应 `property-decorator.ts` + `reflect-metadata-demo.ts`）

实现三个属性装饰器：`@Required`、`@Max(n)`、`@Min(n)`，再写一个 `validate(instance)` 函数，扫描类原型上所有这些元数据，返回错误列表。要求：

```ts
class CreateUserDTO {
  @Required name: string;
  @Min(0) @Max(120) age: number;
}

const errors = validate({ name: '', age: -1 });   // ['name 不能为空', 'age 不能小于 0']
```

提示：在 `target`（原型）上用 `Reflect.defineMetadata` 维护一个 `{ field, rule, params }[]` 数组，`validate` 时遍历它。

**进阶**：用 `design:type` 让 `@Required` 对 `string` 判空字符串、对 `number` 判 `null/undefined`、对 `Array` 判 `length === 0`。

### 练习 3：扩展迷你 DI 容器（对应 `mini-di-container.ts`）

在 `mini-di-container.ts` 基础上扩展：

1. **`useValue` Provider**：`container.register('Config', { useValue: { port: 3000 } })`，`resolve` 时直接返回该值。
2. **`useFactory` Provider**：`container.register('DbClient', { useFactory: (logger) => new DbClient(logger), inject: ['Logger'] })`，工厂自身可声明依赖。
3. **循环依赖检测**：`resolve` 期间维护一个“正在解析”栈，若再次遇到同 token，抛出 `Circular dependency detected: A -> B -> A`。
4. **`@Optional()` 参数装饰器**：标记该参数可选，找不到 Provider 时不抛错而传 `undefined`。

完成后再回头看 NestJS 的 Provider 文档，你会发现 NestJS 的 `useClass / useValue / useFactory / useExisting` 与你写的容器几乎一一对应。

---

## 配套代码

| 文件 | 内容 |
|------|------|
| `Code/class-decorator.ts` | 类装饰器、原型扩展、返回新构造函数、`@Sealed` + `@Logged` 组合、元数据贴标签 |
| `Code/method-decorator.ts` | 方法装饰器、`@Log` 切面（同步/异步）、`@ReadOnly` 只读化、`@Once` 返回新描述符、静态 vs 实例 target |
| `Code/property-decorator.ts` | 属性装饰器、`@TypeLog` 读取 `design:type`、`@Required` 校验标签、`@Trim` 植入 getter/setter |
| `Code/parameter-decorator.ts` | 参数装饰器、索引标记、NestJS 风格 `@Param/@Body/@Query`、构造函数 `@Inject` |
| `Code/decorator-factory.ts` | 装饰器工厂、`@RequireRole`/`@Defaults`/`@MaxLength`/`@Min`、求值与执行顺序、通用工厂 |
| `Code/reflect-metadata-demo.ts` | reflect-metadata 基本 API、`design:type/paramtypes/returntype`、未装饰目标拿不到元数据、key 集中管理 |
| `Code/mini-di-container.ts` | 迷你 DI 容器、`@Injectable` + `@Inject`、`design:paramtypes` 自动装配、单例、token 覆盖 |
| `Code/mini-controller.ts` | 迷你路由装饰器、`@Controller/@Get/@Post/@Put/@Delete` + `@Param/@Body/@Query`、Router 注册表与 dispatch |

运行方式（需先在 `Code/` 目录执行 `npm install`）：

```bash
cd Code
npm install
npx ts-node class-decorator.ts
npx ts-node method-decorator.ts
npx ts-node property-decorator.ts
npx ts-node parameter-decorator.ts
npx ts-node decorator-factory.ts
npx ts-node reflect-metadata-demo.ts
npx ts-node mini-di-container.ts
npx ts-node mini-controller.ts
```

或使用 `package.json` 中预置的脚本：

```bash
npm run class         # 等价于 ts-node class-decorator.ts
npm run method
npm run property
npm run parameter
npm run factory
npm run reflect
npm run di
npm run controller
npm run type-check    # 全量类型检查（不输出文件）
```

---

> 📚 **延伸阅读**
> - TS 官方手册：[Decorators](https://www.typescriptlang.org/docs/handbook/decorators.html)（旧实验性装饰器，本篇所用）
> - TS 官方博客：[TypeScript 5.0 Release Notes - Decorators](https://devblogs.microsoft.com/typescript/announcing-typescript-5-0/#decorators)（stage 3 装饰器）
> - TC39 提案：[tc39/proposal-decorators](https://github.com/tc39/proposal-decorators)
> - reflect-metadata：[npm: reflect-metadata](https://www.npmjs.com/package/reflect-metadata)
> - NestJS 官方文档：[Providers](https://docs.nestjs.com/providers) / [Controllers](https://docs.nestjs.com/controllers) / [Custom Decorators](https://docs.nestjs.com/custom-decorators)
> - 社区文章：[AOP in TypeScript with Decorators](https://basarat.gitbook.io/typescript/type-system/decorators)
