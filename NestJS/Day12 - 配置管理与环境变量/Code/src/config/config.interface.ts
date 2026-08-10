/**
 * Day12 强类型配置接口
 *
 * 设计目标：
 *   1. 让 ConfigService.get<T>() 的返回值有明确类型，避免 any
 *   2. 集中描述项目所有配置项的"形状"，作为团队协作的契约
 *   3. 与 registerAs() 创建的命名空间一一对应
 *
 * 使用方式：
 *   const host = configService.get<string>('database.host');          // 嵌套路径
 *   const appCfg = configService.get<AppConfig>('app');               // 整块读取
 *   const dbCfg = configService.get<DatabaseConfig>('database');
 */

/** 应用层配置（对应 registerAs('app')） */
export interface AppConfig {
  /** 应用名称 */
  name: string;
  /** 监听端口 */
  port: number;
  /** 全局路由前缀，例如 api/v1 */
  prefix: string;
  /** 当前运行环境：development / production / test */
  env: string;
}

/** 数据库配置（对应 registerAs('database')） */
export interface DatabaseConfig {
  host: string;
  port: number;
  username: string;
  password: string;
  database: string;
  /** 完整连接 URL，优先级高于单字段 */
  url: string;
  /** 是否开启 schema 同步（仅开发环境使用） */
  sync: boolean;
}

/** JWT 配置（对应 registerAs('jwt')） */
export interface JwtConfig {
  /** 签名密钥，生产环境必须从 CI 注入 */
  secret: string;
  /** Access Token 过期时间 */
  expiresIn: string;
  /** Refresh Token 过期时间 */
  refreshExpiresIn: string;
}

/** 日志配置（直接从 process.env 读取，未单独命名空间） */
export interface LogConfig {
  level: 'debug' | 'verbose' | 'log' | 'warn' | 'error';
}

/**
 * 全局配置根接口
 * ConfigService.get<RootConfig>() 可以拿到完整配置树
 */
export interface RootConfig {
  app: AppConfig;
  database: DatabaseConfig;
  jwt: JwtConfig;
  log: LogConfig;
}
