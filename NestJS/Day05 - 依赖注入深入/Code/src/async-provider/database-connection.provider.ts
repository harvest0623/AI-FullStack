import { Logger } from '@nestjs/common';

/**
 * 异步 Provider 演示：模拟数据库连接的异步初始化。
 *
 * 在 NestJS 中，useFactory 可以返回 Promise，容器会等待其 resolve
 * 后才把 resolve 出来的值作为该 Token 的实例注入到消费者中。
 *
 * 典型场景：
 *   - 数据库连接池初始化（TypeORM / mongoose）
 *   - 启动时从远程拉取配置
 *   - 初始化 Redis 客户端、消息队列连接
 *
 * 注册写法（见 app.module.ts）：
 *   {
 *     provide: DATABASE_CONNECTION,
 *     useFactory: async () => {
 *       const connection = await createDatabaseConnection();
 *       return connection;
 *     },
 *   }
 */

// 用 Symbol 作为 Token，避免与未来真实的 DB_CONNECTION 冲突
export const DATABASE_CONNECTION = Symbol('DATABASE_CONNECTION');

// 模拟一个数据库连接对象
export interface DatabaseConnection {
  host: string;
  port: number;
  connectedAt: number;
  query<T = unknown>(sql: string): Promise<T[]>;
}

/**
 * 工厂函数：模拟异步建立数据库连接。
 * 真实项目中此处会调用 typeorm.createConnection / mongoose.connect 等。
 */
export async function createDatabaseConnection(): Promise<DatabaseConnection> {
  const logger = new Logger('DatabaseProvider');
  logger.log('开始建立数据库连接...');
  // 模拟连接耗时
  await new Promise((resolve) => setTimeout(resolve, 300));
  const connection: DatabaseConnection = {
    host: '127.0.0.1',
    port: 3306,
    connectedAt: Date.now(),
    async query<T = unknown>(sql: string): Promise<T[]> {
      logger.log(`执行 SQL: ${sql}`);
      return [] as T[];
    },
  };
  logger.log('数据库连接已建立');
  return connection;
}
