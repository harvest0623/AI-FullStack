/**
 * 动态模块 ConfigModule 的配置接口
 *
 * 这是调用方传入的 options，决定了动态模块运行时如何注册 Provider。
 * 真实场景下可包含：envFilePath、isGlobal、cache、validate 等字段。
 */
export interface ConfigModuleOptions {
  /**
   * 是否注册为全局模块。
   * 为 true 时，ConfigService 在全应用可见，无需在每个特性模块再 import 一次。
   */
  isGlobal?: boolean;

  /**
   * 内置的配置项初始值（演示用，简化版）。
   * 真实场景一般从 .env 文件读取。
   */
  config?: Record<string, unknown>;
}

/**
 * 应用运行时配置的形状约束（演示用，可按需扩展）。
 */
export interface AppConfig {
  appName: string;
  port: number;
  [key: string]: unknown;
}
