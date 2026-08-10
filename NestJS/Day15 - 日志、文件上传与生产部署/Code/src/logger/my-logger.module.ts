import { Global, Module } from '@nestjs/common';
import { MyLoggerService } from './my-logger.service';

/**
 * Logger 模块
 *
 * 用 @Global 声明为全局模块，避免每个模块都要在 imports 里加一遍。
 * 注册 MyLoggerService 作为可注入 Provider，其它地方直接构造函数注入即可。
 *
 * 注意：
 *   - 在 main.ts 中 app.useLogger(app.get(MyLoggerService)) 之后，
 *     NestJS 内置 Logger 也会转发到本服务，所有 .log/.error 自动落盘。
 *   - 业务代码里若需要 context 标识，可手动 new MyLoggerService(MyService.name)，
 *     但要小心：手动 new 出来的实例不会共享容器单例。
 */
@Global()
@Module({
  providers: [MyLoggerService],
  exports: [MyLoggerService],
})
export class MyLoggerModule {}
