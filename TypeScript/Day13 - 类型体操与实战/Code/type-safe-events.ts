/**
 * Day13 - 类型体操实战 06：类型安全的事件系统
 *
 * 本文件实现一个 EventEmitter：on / off / emit 三个方法全部“类型安全”。
 *  - 注册事件时，事件名和回调参数类型必须严格匹配预定义的 EventMap
 *  - 触发事件时，传入的参数类型也必须匹配
 *
 * 核心思路：用泛型 + keyof + 索引访问把 EventMap 当作“事件字典”，
 *           让每个 API 的参数都从字典中精确推导。
 */

export {};

// ============================================================
// 1. 定义事件字典（EventMap）
// ============================================================

// 用 interface 定义“事件名 → 载荷类型”的映射
// 载荷类型就是回调函数接收的参数
interface AppEvents {
  'user:login':     { userId: string; loginAt: Date };
  'user:logout':    { userId: string };
  'message:new':    { messageId: string; content: string; from: string };
  'error':          { code: number; message: string };
  'ready':          undefined;   // 无载荷
}


// ============================================================
// 2. 类型安全 EventEmitter 实现
// ============================================================

class TypedEmitter<Events extends Record<string, any>> {
  // 内部存储：事件名 → 回调函数数组
  // 回调签名由 Events[K] 决定，运行时按字符串 key 分组存储
  private listeners: { [K in keyof Events]?: Array<(payload: Events[K]) => void> } = {};

  /**
   * 注册事件监听器
   * @param event  事件名，必须是 Events 的键
   * @param handler 回调，参数类型严格匹配 Events[Event]
   */
  on<K extends keyof Events>(event: K, handler: (payload: Events[K]) => void): this {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event]!.push(handler);
    return this;
  }

  /**
   * 注销事件监听器
   * 传入的 handler 必须与 on 注册时的引用一致才能正确移除
   */
  off<K extends keyof Events>(event: K, handler: (payload: Events[K]) => void): this {
    const arr = this.listeners[event];
    if (!arr) return this;
    const idx = arr.indexOf(handler);
    if (idx >= 0) arr.splice(idx, 1);
    return this;
  }

  /**
   * 触发事件
   * 传入的 payload 类型必须严格匹配 Events[Event]
   */
  emit<K extends keyof Events>(event: K, ...args: Events[K] extends undefined ? [] : [payload: Events[K]]): this {
    const arr = this.listeners[event];
    if (!arr) return this;
    // 无载荷事件：args 为空元组；有载荷事件：args[0] 为 payload
    const payload = args[0] as Events[K];
    arr.forEach((fn) => fn(payload));
    return this;
  }

  /**
   * 一次性监听：触发一次后自动注销
   */
  once<K extends keyof Events>(event: K, handler: (payload: Events[K]) => void): this {
    const wrapper = (payload: Events[K]) => {
      handler(payload);
      this.off(event, wrapper as (p: Events[K]) => void);
    };
    return this.on(event, wrapper);
  }

  /**
   * 清空某事件的所有监听器（不传则清空全部）
   */
  removeAllListeners<K extends keyof Events>(event?: K): this {
    if (event) {
      delete this.listeners[event];
    } else {
      this.listeners = {};
    }
    return this;
  }
}


// ============================================================
// 3. 实战：用 AppEvents 实例化一个事件总线
// ============================================================

const bus = new TypedEmitter<AppEvents>();

// 注册监听器：参数类型自动推断
bus.on('user:login', (payload) => {
  // ✅ payload 类型为 { userId: string; loginAt: Date }
  console.log('[事件] user:login =>', payload.userId, 'at', payload.loginAt.toISOString());
  // payload.messageId;  // ❌ 不存在该属性
});

bus.on('message:new', (payload) => {
  // ✅ payload 类型为 { messageId; content; from }
  console.log('[事件] message:new =>', `[${payload.from}] ${payload.content}`);
});

bus.on('error', (payload) => {
  console.log('[事件] error =>', payload.code, payload.message);
});

bus.on('ready', () => {
  console.log('[事件] ready => 系统就绪');
});

// 触发：参数类型严格校验
bus.emit('user:login', { userId: 'u-001', loginAt: new Date() });
bus.emit('message:new', { messageId: 'm-1', content: 'Hello', from: 'Alice' });
bus.emit('error', { code: 500, message: 'Internal Server Error' });
bus.emit('ready');      // 无载荷事件

// 类型错误的触发会被编译器拦截：
// bus.emit('user:login', { userId: 'u-001' });                 // ❌ 缺 loginAt
// bus.emit('message:new', { messageId: 'm-1', content: 'x' }); // ❌ 缺 from
// bus.emit('unknown', {});                                      // ❌ 事件名不在 AppEvents 中


// ============================================================
// 4. 一次性监听 + 注销
// ============================================================

bus.once('user:logout', (payload) => {
  console.log('[事件 once] user:logout =>', payload.userId);
});

bus.emit('user:logout', { userId: 'u-001' });   // ✅ 触发
bus.emit('user:logout', { userId: 'u-002' });   // ⚠️ 已注销，无输出

const handler = (payload: { userId: string }) => {
  console.log('[事件 off] 仍监听中 =>', payload.userId);
};
bus.on('user:logout', handler);
bus.emit('user:logout', { userId: 'u-003' });   // ✅ 触发
bus.off('user:logout', handler);
bus.emit('user:logout', { userId: 'u-004' });   // ⚠️ 已 off，无输出


// ============================================================
// 5. 进阶：从对象自动生成事件名 + 载荷类型
// ============================================================

// 场景：给定一个 store，自动生成 'change:<field>' 事件
interface Store {
  count: number;
  name: string;
}

// 用模板字面量类型生成事件名联合
type StoreEvents<T> = {
  [K in keyof T & string as `change:${K}`]: { oldValue: T[K]; newValue: T[K] };
};

type DerivedEvents = StoreEvents<Store>;
// { 'change:count': { oldValue: number; newValue: number };
//   'change:name':  { oldValue: string; newValue: string } }

const storeBus = new TypedEmitter<DerivedEvents>();

storeBus.on('change:count', (e) => {
  console.log('[派生事件] count:', e.oldValue, '→', e.newValue);
});
storeBus.on('change:name', (e) => {
  console.log('[派生事件] name:', e.oldValue, '→', e.newValue);
});

storeBus.emit('change:count', { oldValue: 0, newValue: 1 });
storeBus.emit('change:name', { oldValue: 'a', newValue: 'b' });
// storeBus.emit('change:count', { oldValue: 0, newValue: '1' });  // ❌ newValue 必须是 number


// ============================================================
// 6. 进阶：链式 API 类型推断
// ============================================================

// 通过返回 this，让 on/off/emit 链式调用都保留完整类型
bus
  .on('ready', () => console.log('[链式] ready'))
  .emit('ready')
  .removeAllListeners('ready');


console.log('\n--- type-safe-events.ts 执行完毕 ---');
