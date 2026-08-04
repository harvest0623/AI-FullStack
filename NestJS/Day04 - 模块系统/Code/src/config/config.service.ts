import { Injectable } from '@nestjs/common';
import { AppConfig, ConfigModuleOptions } from './config.interface';

/**
 * ConfigService
 *
 * 由动态模块 ConfigModule.forRoot 在运行时实例化并注册到 DI 容器。
 * 由于 forRoot 返回的 DynamicModule 中 providers 使用了 useValue 形式，
 * 这里仍用 @Injectable 标注以保持类型可注入。
 */
@Injectable()
export class ConfigService {
  private readonly config: AppConfig;

  constructor(options: ConfigModuleOptions = {}) {
    // 把内置默认值与调用方传入的 config 合并，模拟"加载配置"的过程
    this.config = {
      appName: 'Day04 Module System',
      port: 3000,
      ...(options.config ?? {}),
    } as AppConfig;
  }

  /**
   * 读取某个配置项
   */
  get<T = unknown>(key: keyof AppConfig | string): T {
    return this.config[key as string] as T;
  }

  /**
   * 返回全部配置（调试用）
   */
  getAll(): AppConfig {
    return this.config;
  }
}
