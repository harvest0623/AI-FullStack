/**
 * async-typed.ts
 * TypeScript 异步类型化：
 *   - Promise<T> 显式标注
 *   - async 函数返回类型推断
 *   - Promise.all 的元组类型保留
 *   - EventEmitter 的类型化事件
 *
 * 运行：tsx async-typed.ts
 */

import { EventEmitter } from 'node:events';
import { readFile } from 'node:fs/promises';

// ============================================================
// 1. Promise<T> 显式标注
// ============================================================

interface User {
  id: number;
  name: string;
  email: string;
}

// 异步函数显式返回 Promise<User>
async function fetchUser(id: number): Promise<User> {
  if (id <= 0) {
    // throw 出去的错误会被 Promise 拒绝
    throw new Error(`非法 id: ${id}`);
  }
  return { id, name: `User-${id}`, email: `user${id}@example.com` };
}

// 不写 return type 时，TS 会自动推断为 Promise<User>
async function fetchUserInferred(id: number) {
  return fetchUser(id);
}

// ============================================================
// 2. Promise.all 元组类型保留：参数顺序 = 类型顺序
// ============================================================

async function loadDashboard(userId: number): Promise<{
  user: User;
  postsCount: number;
  lastLogin: Date;
}> {
  // Promise.all 接收元组，返回元组类型，顺序严格保留
  const [user, postsCount, lastLogin] = await Promise.all([
    fetchUser(userId),                          // Promise<User>
    Promise.resolve(42),                        // Promise<number>
    Promise.resolve(new Date('2026-07-25')),    // Promise<Date>
  ]);

  // 此时类型已经是 [User, number, Date]
  return { user, postsCount, lastLogin };
}

// ============================================================
// 3. Promise.allSettled：部分失败时的类型化
// ============================================================

interface SettledResult<T> {
  ok: boolean;
  value?: T;
  reason?: string;
}

async function fetchUsers(ids: number[]): Promise<SettledResult<User>[]> {
  const results = await Promise.allSettled(ids.map(fetchUser));

  // results 类型是 PromiseSettledResult<User>[]
  return results.map<SettledResult<User>>((r) => {
    if (r.status === 'fulfilled') {
      return { ok: true, value: r.value };
    }
    // r.status === 'rejected' 时 r.reason 是 unknown
    const reason: string = r.reason instanceof Error ? r.reason.message : String(r.reason);
    return { ok: false, reason };
  });
}

// ============================================================
// 4. EventEmitter 的类型化事件
// ============================================================

// 方式一：声明式 EventMap
interface TaskEvents {
  start: { taskId: number; at: Date };
  progress: { taskId: number; percent: number };
  done: { taskId: number; result: string };
  error: { taskId: number; err: Error };
}

/**
 * 严格类型的 EventEmitter：用泛型把 on/emit 收窄到合法事件名 + payload 类型
 */
class TypedEmitter<E extends Record<string, any>> extends EventEmitter {
  emit<K extends keyof E & string>(event: K, payload: E[K]): boolean {
    return super.emit(event, payload);
  }

  on<K extends keyof E & string>(event: K, listener: (payload: E[K]) => void): this {
    return super.on(event, listener);
  }

  once<K extends keyof E & string>(event: K, listener: (payload: E[K]) => void): this {
    return super.once(event, listener);
  }
}

class TaskRunner extends TypedEmitter<TaskEvents> {
  async run(taskId: number): Promise<void> {
    this.emit('start', { taskId, at: new Date() });

    for (const percent of [25, 50, 75, 100]) {
      await new Promise<void>((resolve) => setTimeout(resolve, 30));
      this.emit('progress', { taskId, percent });
    }

    this.emit('done', { taskId, result: `任务 ${taskId} 完成` });
  }
}

// ============================================================
// 5. async/await + try/catch（unknown 收窄）
// ============================================================

async function readConfig(path: string): Promise<Record<string, unknown>> {
  try {
    const raw: string = await readFile(path, 'utf8');
    return JSON.parse(raw) as Record<string, unknown>;
  } catch (err: unknown) {
    // err 是 unknown，必须收窄
    if (err instanceof Error) {
      console.error(`[readConfig] 失败: ${err.message}`);
    } else {
      console.error('[readConfig] 未知错误:', err);
    }
    throw err; // 继续向上抛
  }
}

// ============================================================
// 6. 演示入口
// ============================================================

async function main(): Promise<void> {
  console.log('--- fetchUser ---');
  const user: User = await fetchUser(7);
  console.log(user);

  console.log('\n--- Promise.all 元组 ---');
  const dashboard = await loadDashboard(7);
  console.log(dashboard);

  console.log('\n--- Promise.allSettled ---');
  const settled = await fetchUsers([1, -2, 3, 0]);
  console.log(settled);

  console.log('\n--- TypedEmitter ---');
  const runner = new TaskRunner();
  runner.on('start', (p) => console.log('  start:', p));
  runner.on('progress', (p) => console.log('  progress:', `${p.percent}%`));
  runner.on('done', (p) => console.log('  done:', p.result));
  await runner.run(101);

  console.log('\n--- readConfig (不存在的文件) ---');
  try {
    await readConfig('./__not_exist__.json');
  } catch {
    // 已在函数内部打印
  }

  console.log('\n[done] async-typed demo finished.');
}

main().catch((err: unknown) => {
  console.error('主流程异常:', err);
  process.exit(1);
});
