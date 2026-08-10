import { ConfigService } from '@nestjs/config';
import { TypeOrmModuleOptions } from '@nestjs/typeorm';
import { Article } from './entities/article.entity';
import { User } from './entities/user.entity';

/**
 * TypeORM 异步配置工厂
 *
 * 通过 ConfigService 读取 .env 中的数据库参数（呼应 Day12 配置体系）：
 *   - DB_DATABASE：SQLite 数据库路径，默认 ':memory:'（内存库）
 *
 * 生产环境务必把 synchronize 设为 false，改用 migration。
 */
export function getTypeOrmConfig(
  configService: ConfigService,
): TypeOrmModuleOptions {
  const isProduction = configService.get<string>('NODE_ENV') === 'production';

  return {
    type: 'sqlite',
    database: configService.get<string>('DB_DATABASE', ':memory:'),
    entities: [Article, User],
    synchronize: !isProduction, // 开发期自动建表，生产期用 migration
    logging: configService.get<string>('DB_LOGGING') === 'true',
  };
}
