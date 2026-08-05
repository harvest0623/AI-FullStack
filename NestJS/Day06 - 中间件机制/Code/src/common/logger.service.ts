import { Injectable } from '@nestjs/common';

// ============================================================
// 简单日志服务
// ------------------------------------------------------------
// 演示要点：
//   1. @Injectable 装饰器声明可被 DI 容器管理
//   2. 被 LoggerMiddleware / AuthMiddleware 类中间件注入
//   3. 类作为 Token，注入时无需 @Inject 装饰器
//
// 在真实项目中通常会直接用 @nestjs/common 内置的 Logger，
// 这里手写一份是为了让中间件的 DI 演示更直观。
// ============================================================

@Injectable()
export class LoggerService {
  private format(message: string, context: string): string {
    const time = new Date().toISOString();
    return `[${time}] [${context}] ${message}`;
  }

  log(message: string, context = 'App'): void {
    console.log(this.format(message, context));
  }

  warn(message: string, context = 'App'): void {
    console.warn(this.format(message, context));
  }

  error(message: string, trace?: string, context = 'App'): void {
    console.error(`${this.format(message, context)}${trace ? `\n${trace}` : ''}`);
  }
}
