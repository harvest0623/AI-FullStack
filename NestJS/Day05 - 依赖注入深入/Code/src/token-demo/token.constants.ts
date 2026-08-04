/**
 * Provider Token 常量定义。
 *
 * NestJS 中所有 Provider 都通过 Token 在 IoC 容器中注册与解析。
 * Token 可以是：
 *   1. 类本身（最常见，配合 emitDecoratorMetadata 自动推断）
 *   2. 字符串（用于值提供者、配置对象）
 *   3. Symbol（强烈推荐用于字符串 Token 的替代，避免命名冲突）
 *   4. 抽象类（用于面向接口编程，便于替换实现）
 *
 * 本文件演示字符串 Token 与 Symbol Token 两种。
 */

// ---------- 字符串 Token ----------
// 注意：字符串 Token 全局命名空间不冲突检测，需自行保证唯一性
export const APP_CONFIG_TOKEN = 'APP_CONFIG';

export interface AppConfig {
  port: number;
  env: 'dev' | 'prod';
  featureFlags: {
    newDashboard: boolean;
  };
}

// ---------- Symbol Token ----------
// Symbol 天然唯一，即使描述相同也不会冲突，是替代字符串 Token 的最佳实践
export const LOGGER_KEY = Symbol('LOGGER');

export interface ILogger {
  log(message: string): void;
  error(message: string): void;
}

// ---------- 抽象类 Token（在 token-demo.controller.ts 中演示） ----------
// 通过抽象类作为 Token，可以面向接口注入，方便切换实现
export abstract class CacheProvider {
  abstract get(key: string): unknown;
  abstract set(key: string, value: unknown): void;
}
