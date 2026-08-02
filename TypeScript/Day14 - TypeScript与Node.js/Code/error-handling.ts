/**
 * error-handling.ts
 * TS 中错误处理的类型化实践：
 *   - useUnknownInCatchVariables：catch 变量是 unknown 而非 any
 *   - 自定义错误类继承 Error
 *   - 错误类型收窄
 *
 * 运行：tsx error-handling.ts
 */

// ============================================================
// 1. 自定义错误类继承 Error
// ============================================================

/**
 * 业务错误基类：所有可控错误都继承自它
 * 注意：extends Error 在 TS 5 + ES2022 target 下，
 *       需要在构造器里手动设置 Object.setPrototypeOf 才能让 instanceof 跨原型链生效
 */
export class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number = 500,
    public readonly details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = 'AppError';
    // 修复 extends Error 后原型链丢失的问题（target < ES2022 必须有）
    Object.setPrototypeOf(this, new.target.prototype);
  }

  toJSON(): Record<string, unknown> {
    return {
      name: this.name,
      code: this.code,
      message: this.message,
      statusCode: this.statusCode,
      details: this.details,
    };
  }
}

export class ValidationError extends AppError {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, 'VALIDATION_ERROR', 400, details);
    this.name = 'ValidationError';
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string) {
    super(`${resource} not found`, 'NOT_FOUND', 404);
    this.name = 'NotFoundError';
  }
}

export class UnauthorizedError extends AppError {
  constructor(message = 'Unauthorized') {
    super(message, 'UNAUTHORIZED', 401);
    this.name = 'UnauthorizedError';
  }
}

// ============================================================
// 2. 错误类型收窄工具
// ============================================================

/** 判断 unknown 是否为 Error 实例 */
function isError(value: unknown): value is Error {
  return value instanceof Error;
}

/** 判断 unknown 是否为 AppError 实例 */
function isAppError(value: unknown): value is AppError {
  return value instanceof AppError;
}

/** 安全读取 unknown 的 message 字段 */
function safeMessage(err: unknown): string {
  if (isError(err)) return err.message;
  if (typeof err === 'string') return err;
  return '未知错误';
}

// ============================================================
// 3. try/catch 在 strict + useUnknownInCatchVariables 下的正确姿势
// ============================================================

function riskyOperation(kind: 'validation' | 'notfound' | 'system'): void {
  switch (kind) {
    case 'validation':
      throw new ValidationError('用户名不能为空', { field: 'username' });
    case 'notfound':
      throw new NotFoundError('User#42');
    case 'system':
      // 模拟系统错误：原生 Error
      throw new Error('ECONNRESET: connection reset by peer');
  }
}

/** 把 unknown 的 catch 错误统一转成 AppError，便于上层处理 */
function normalizeError(err: unknown): AppError {
  if (isAppError(err)) return err;
  if (isError(err)) {
    return new AppError(err.message, 'INTERNAL_ERROR', 500);
  }
  return new AppError(safeMessage(err), 'UNKNOWN_ERROR', 500);
}

function handleOperation(kind: 'validation' | 'notfound' | 'system'): void {
  try {
    riskyOperation(kind);
    console.log(`[${kind}] 成功`);
  } catch (err: unknown) {
    // err 是 unknown，不能直接 err.message（编译报错）
    // 必须先收窄
    const appErr = normalizeError(err);
    console.log(`[${kind}] 捕获到错误:`);
    console.log('  name       =', appErr.name);
    console.log('  code       =', appErr.code);
    console.log('  statusCode =', appErr.statusCode);
    console.log('  message    =', appErr.message);
    if (appErr.details) {
      console.log('  details    =', appErr.details);
    }
  }
}

// ============================================================
// 4. 错误类型收窄：基于 code 的判别联合
// ============================================================

type RpcError =
  | { kind: 'network'; reason: string }
  | { kind: 'timeout'; ms: number }
  | { kind: 'protocol'; code: number };

function describeRpcError(err: RpcError): string {
  switch (err.kind) {
    case 'network':
      return `网络错误: ${err.reason}`;
    case 'timeout':
      return `超时: ${err.ms}ms`;
    case 'protocol':
      return `协议错误码: ${err.code}`;
  }
}

// ============================================================
// 5. 演示入口
// ============================================================

console.log('--- ValidationError ---');
handleOperation('validation');

console.log('\n--- NotFoundError ---');
handleOperation('notfound');

console.log('\n--- System Error ---');
handleOperation('system');

console.log('\n--- 判别联合收窄 ---');
const errors: RpcError[] = [
  { kind: 'network', reason: 'ECONNREFUSED' },
  { kind: 'timeout', ms: 3000 },
  { kind: 'protocol', code: 502 },
];
for (const e of errors) {
  console.log(' -', describeRpcError(e));
}

console.log('\n--- JSON.stringify(AppError) ---');
const sample: AppError = new ValidationError('邮箱格式错误', { field: 'email' });
console.log(JSON.stringify(sample.toJSON(), null, 2));
