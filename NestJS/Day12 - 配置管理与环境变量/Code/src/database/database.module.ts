import { Module } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { DatabaseConfig } from '../config/config.interface';

/**
 * Day12 数据库模块（演示读取配置）
 *
 * 这里不真正连接数据库（Day13 才会接入 TypeORM），
 * 只演示：
 *   1. 在动态模块 / Provider 中通过 ConfigService 拿到数据库连接参数
 *   2. 通过强类型接口 DatabaseConfig 让 get<T>() 的返回值有类型
 *
 * 真实场景中，TypeORM 的 forRootAsync 用法如下（Day13 会实现）：
 *
 *   TypeOrmModule.forRootAsync({
 *     inject: [ConfigService],
 *     useFactory: (config: ConfigService) => ({
 *       type: 'postgres',
 *       host: config.get<string>('database.host'),
 *       port: config.get<number>('database.port'),
 *       username: config.get<string>('database.username'),
 *       password: config.get<string>('database.password'),
 *       database: config.get<string>('database.database'),
 *       synchronize: config.get<boolean>('database.sync'),
 *     }),
 *   })
 *
 * 此处用 provider + useFactory 把连接配置打印出来，证明配置链路通了。
 */
@Module({
  providers: [
    {
      // 提供一个"数据库连接配置"令牌，方便其他模块注入
      provide: 'DATABASE_CONFIG',
      inject: [ConfigService],
      useFactory: (configService: ConfigService): DatabaseConfig => {
        const dbConfig: DatabaseConfig = {
          host: configService.get<string>('database.host', 'localhost'),
          port: configService.get<number>('database.port', 5432),
          username: configService.get<string>('database.username', 'postgres'),
          password: configService.get<string>('database.password', ''),
          database: configService.get<string>('database.database', 'nest_app'),
          url: configService.get<string>('database.url', ''),
          sync: configService.get<boolean>('database.sync', false),
        };

        // 演示：启动时打印一次（生产环境应改为 debug 级别，避免泄露密码）
        // eslint-disable-next-line no-console
        console.log('[DatabaseModule] 已加载配置 ->', {
          host: dbConfig.host,
          port: dbConfig.port,
          database: dbConfig.database,
          sync: dbConfig.sync,
          // 密码不打印明文
          hasPassword: Boolean(dbConfig.password),
          hasUrl: Boolean(dbConfig.url),
        });

        return dbConfig;
      },
    },
  ],
  exports: ['DATABASE_CONFIG'],
})
export class DatabaseModule {}
