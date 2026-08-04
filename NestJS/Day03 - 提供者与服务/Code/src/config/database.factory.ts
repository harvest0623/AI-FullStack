// ============================================================
// useFactory 演示：工厂提供者
// ------------------------------------------------------------
// 工厂函数可以：
//   1. 异步初始化（await 数据库连接、读取远程配置）
//   2. 依赖其他 Provider（通过 inject 数组声明）
//   3. 根据运行时条件返回不同实现
// ============================================================

import { AppConfig } from './config.provider';

// 工厂创建出的数据库连接对象
export interface DatabaseConnection {
  host: string;
  port: number;
  connectedAt: Date;
  query: (sql: string) => Promise<string>;
  close: () => Promise<void>;
}

// useFactory 引用的工厂函数
// 模拟异步建立数据库连接的过程，并依赖 AppConfig 决定连接地址
export async function createDatabaseConnection(
  config: AppConfig,
): Promise<DatabaseConnection> {
  // 模拟异步连接耗时
  await new Promise((resolve) => setTimeout(resolve, 100));

  console.log(`[Database] 已连接到 ${config.dbHost}:${config.dbPort}`);

  return {
    host: config.dbHost,
    port: config.dbPort,
    connectedAt: new Date(),
    async query(sql: string) {
      return `[Result] execute: ${sql}`;
    },
    async close() {
      console.log(`[Database] 已断开 ${config.dbHost}:${config.dbPort}`);
    },
  };
}
