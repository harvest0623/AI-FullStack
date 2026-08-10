/**
 * 根配置加载函数
 *
 * 用途：
 *   在 ConfigModule.forRoot({ load: [configuration] }) 中被调用，
 *   把 process.env 中"扁平"的环境变量整理成一棵"嵌套"配置树。
 *
 * 与 registerAs() 的关系：
 *   - configuration.ts 是兜底的全局配置，可通过 configService.get('app.port') 读取
 *   - registerAs('app') 是命名空间配置，覆盖更具体、类型更明确
 *   - 两者并存时，命名空间的优先级更高、可读性更好
 *
 * 注意：
 *   - 这里只读取已校验过的字段（Joi 已在 forRoot 中校验过）
 *   - 数字类型需要手动转换（dotenv 读出来的都是 string）
 */
export const configuration = () => ({
  // 应用层
  app: {
    name: process.env.APP_NAME || 'nest-app',
    port: parseInt(process.env.APP_PORT || '3000', 10),
    prefix: process.env.APP_PREFIX || 'api/v1',
    env: process.env.NODE_ENV || 'development',
  },

  // 数据库
  database: {
    host: process.env.DATABASE_HOST || 'localhost',
    port: parseInt(process.env.DATABASE_PORT || '5432', 10),
    username: process.env.DATABASE_USERNAME || 'postgres',
    password: process.env.DATABASE_PASSWORD || '',
    database: process.env.DATABASE_NAME || 'nest_app',
    url: process.env.DATABASE_URL || '',
    sync: process.env.DATABASE_SYNC === 'true',
  },

  // JWT
  jwt: {
    secret: process.env.JWT_SECRET || '',
    expiresIn: process.env.JWT_EXPIRES_IN || '1h',
    refreshExpiresIn: process.env.JWT_REFRESH_EXPIRES_IN || '7d',
  },

  // 日志
  log: {
    level: process.env.LOG_LEVEL || 'log',
  },
});
