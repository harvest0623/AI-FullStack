import { Global, Module } from '@nestjs/common';
import { LoggerService } from './logger.service';

/**
 * 全局模块 CommonModule
 *
 * @Global() 装饰器使此模块的 exports 在整个应用可见：
 * - 只需在 AppModule imports 一次
 * - 任意模块的 Provider 都可以直接注入 LoggerService，无需在自己的 imports 里再写 CommonModule
 *
 * 适合放真正全局通用的 Provider：日志、配置、缓存等。
 * 滥用 @Global 会破坏模块边界，请克制使用。
 */
@Global()
@Module({
  providers: [LoggerService],
  exports: [LoggerService],
})
export class CommonModule {}
