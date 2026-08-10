import { registerAs } from '@nestjs/config';

/**
 * 数据库配置命名空间
 *
 * registerAs('database') 创建 'database' 命名空间：
 *   configService.get('database.host')  -> 'localhost'
 *   configService.get('database.url')   -> 'postgresql://...'
 *
 * 注意点：
 *   1. 字符串 'database' 与 config.interface.ts 的 DatabaseConfig 对齐
 *   2. 数字字段（port）必须显式 parseInt，dotenv 默认全是 string
 *   3. 布尔字段（sync）用 === 'true' 比较，避免 'false' 被当作 truthy
 *   4. 生产环境的 sync 必须为 false，否则会自动改表结构造成事故
 *
 * Day13 会用这里的字段配置 TypeORM，本 Day 仅做读取演示。
 */
export const databaseConfig = registerAs('database', () => ({
  host: process.env.DATABASE_HOST || 'localhost',
  port: parseInt(process.env.DATABASE_PORT || '5432', 10),
  username: process.env.DATABASE_USERNAME || 'postgres',
  password: process.env.DATABASE_PASSWORD || '',
  database: process.env.DATABASE_NAME || 'nest_app',
  url: process.env.DATABASE_URL || '',
  sync: process.env.DATABASE_SYNC === 'true',
}));

export type DatabaseConfigType = typeof databaseConfig;
