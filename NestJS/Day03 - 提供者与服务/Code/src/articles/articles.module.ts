// ============================================================
// ArticlesModule：文章模块
// ------------------------------------------------------------
// 演示要点：
//   1. 模块的 providers 数组是注册 Provider 的标准位置
//   2. 同一模块内注册的 Provider 可互相注入
//   3. 集中演示 useClass / useValue / useFactory 三种注册方式
// ============================================================

import { Module } from '@nestjs/common';
import { LoggerService } from '../common/logger.service';
import { AppConfig, appConfig } from '../config/config.provider';
import {
  createDatabaseConnection,
  DatabaseConnection,
} from '../config/database.factory';
import {
  CONFIG_TOKEN,
  DATABASE_CONNECTION_TOKEN,
} from '../config/token.constants';
import { ArticlesController } from './articles.controller';
import { ArticlesService } from './articles.service';

@Module({
  controllers: [ArticlesController],
  providers: [
    // ① 简写：直接写类名，等价于 { provide: ArticlesService, useClass: ArticlesService }
    ArticlesService,

    // ② 简写：LoggerService（被 ArticlesService 注入，演示 Service 间依赖）
    LoggerService,

    // ③ useValue：配置对象（字符串 Token）
    {
      provide: CONFIG_TOKEN,
      useValue: appConfig,
    },

    // ④ useFactory：异步工厂，依赖 CONFIG_TOKEN
    //    inject 数组声明工厂参数对应的 Token，容器会先解析依赖再调用工厂
    {
      provide: DATABASE_CONNECTION_TOKEN,
      useFactory: async (config: AppConfig): Promise<DatabaseConnection> =>
        createDatabaseConnection(config),
      inject: [CONFIG_TOKEN],
    },
  ],
})
export class ArticlesModule {}
