// ============================================================
// 简单日志服务
// ------------------------------------------------------------
// 演示要点：
//   1. @Injectable 装饰器声明可被 DI 容器管理
//   2. 被 ArticlesService 注入，演示 Service 之间的依赖
//   3. 类作为 Token，注入时无需 @Inject
// ============================================================

import { Injectable } from '@nestjs/common';

@Injectable()
export class LoggerService {
  log(message: string, context = 'App'): void {
    const time = new Date().toISOString();
    console.log(`[${time}] [${context}] ${message}`);
  }

  error(message: string, trace?: string): void {
    console.error(`[ERROR] ${message}${trace ? `\n${trace}` : ''}`);
  }

  warn(message: string): void {
    console.warn(`[WARN] ${message}`);
  }
}
