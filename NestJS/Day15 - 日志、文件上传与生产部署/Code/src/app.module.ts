import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { ScheduleModule } from '@nestjs/schedule';
import { TerminusModule } from '@nestjs/terminus';
import { ThrottlerModule, ThrottlerGuard } from '@nestjs/throttler';
import { APP_GUARD } from '@nestjs/core';

import { AppController } from './app.controller';
import { MyLoggerModule } from './logger/my-logger.module';
import { UploadModule } from './upload/upload.module';
import { TasksModule } from './tasks/tasks.module';
import { HealthModule } from './health/health.module';

/**
 * Day15 根模块
 *
 * 汇总生产级应用所需的"基础设施"模块：
 *   - ConfigModule：环境变量加载
 *   - ScheduleModule：定时任务
 *   - TerminusModule：健康检查
 *   - ThrottlerModule：限流（默认 60s 内 100 次）
 *   - 业务模块：Upload / Tasks / Health / Logger
 *
 * ThrottlerGuard 通过 APP_GUARD 注册为全局守卫，
 * 所有路由自动应用限流策略，无需逐个 @UseGuards。
 */
@Module({
  imports: [
    // 1) 环境变量：全局可见，加载 .env 文件
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: ['.env'],
      ignoreEnvFile: process.env.NODE_ENV === 'production',
    }),

    // 2) 定时任务：必须 forRoot 一次，全局生效
    ScheduleModule.forRoot(),

    // 3) 健康检查模块
    TerminusModule,

    // 4) 限流：默认 TTL=60s / LIMIT=100，可按需调整
    ThrottlerModule.forRootAsync({
      inject: [ConfigService],
      useFactory: (config: ConfigService) => [
        {
          ttl: config.get<number>('THROTTLE_TTL', 60000),
          limit: config.get<number>('THROTTLE_LIMIT', 100),
        },
      ],
    }),

    // 5) 自定义模块
    MyLoggerModule,
    UploadModule,
    TasksModule,
    HealthModule,
  ],
  controllers: [AppController],
  providers: [
    // 全局限流守卫：所有路由自动套用
    {
      provide: APP_GUARD,
      useClass: ThrottlerGuard,
    },
  ],
})
export class AppModule {}
