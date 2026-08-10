import { Module } from '@nestjs/common';
import { TerminusModule } from '@nestjs/terminus';
import { HealthController } from './health.controller';

/**
 * 健康检查模块
 *
 * TerminusModule 已在 AppModule 全局注册，这里再 import 一次只是为了
 * 显式表达依赖关系（不影响功能）。Controller 注册到本模块即可被路由扫描到。
 */
@Module({
  imports: [TerminusModule],
  controllers: [HealthController],
})
export class HealthModule {}
