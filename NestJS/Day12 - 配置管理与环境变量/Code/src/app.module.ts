import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { ArticlesModule } from './articles/articles.module';
import { DatabaseModule } from './database/database.module';
import { configuration } from './config/configuration';
import { appConfig } from './config/app.config';
import { databaseConfig } from './config/database.config';
import { jwtConfig } from './config/jwt.config';
import { validationSchema } from './config/validation.schema';

/**
 * Day12 根模块
 *
 * ConfigModule.forRoot 关键选项说明：
 *
 *   isGlobal: true
 *     - ConfigModule 注册为全局模块
 *     - 任何模块注入 ConfigService 都无需再 import ConfigModule
 *
 *   envFilePath
 *     - 根据 NODE_ENV 切换 .env 文件
 *     - 不传则默认加载根目录的 .env
 *     - 数组形式可同时加载多个文件，先加载的优先级低
 *
 *   load: [configuration, appConfig, databaseConfig, jwtConfig]
 *     - 加载根配置函数 + 三个命名空间配置
 *     - 命名空间配置在 configService 中以 'app' / 'database' / 'jwt' 为键
 *
 *   validationSchema
 *     - Joi schema，启动时校验 process.env
 *
 *   validationOptions
 *     - abortEarly: false -> 一次性报告所有错误，而非遇到第一个就停
 *     - allowUnknown: true -> 允许 .env 中存在 schema 未声明的字段
 *     - stripUnknown: false -> 不删除未声明字段（保留原值）
 *
 *   cache: true
 *     - 配置读取结果缓存，避免重复解析（默认即开启）
 *
 *   expandVariables: true
 *     - 支持 .env 内变量展开，例如：
 *       DATABASE_URL=postgresql://$DATABASE_USERNAME:$DATABASE_PASSWORD@...
 */
@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: [
        // 数组中靠后的文件优先级更高（会覆盖前面的同名变量）
        '.env',
        `.env.${process.env.NODE_ENV || 'development'}`,
      ],
      load: [configuration, appConfig, databaseConfig, jwtConfig],
      validationSchema,
      validationOptions: {
        abortEarly: false,
        allowUnknown: true,
        stripUnknown: false,
      },
      cache: true,
      expandVariables: true,
    }),
    ArticlesModule,
    DatabaseModule,
  ],
})
export class AppModule {}
