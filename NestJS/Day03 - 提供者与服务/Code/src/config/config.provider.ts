// ============================================================
// useValue 演示：配置对象作为 Provider
// ------------------------------------------------------------
// 把"配置"也变成可注入的东西，是 NestJS DI 的常见用法。
// 这里定义配置的类型与具体值，由模块用 useValue 注册到容器。
// ============================================================

// 配置对象的类型契约
export interface AppConfig {
  port: number;
  environment: 'development' | 'production';
  apiPrefix: string;
  dbHost: string;
  dbPort: number;
}

// useValue 提供的具体配置值
// 实际项目里这部分常来自 .env / 远程配置中心
export const appConfig: AppConfig = {
  port: 3000,
  environment: 'development',
  apiPrefix: 'api',
  dbHost: 'localhost',
  dbPort: 5432,
};
