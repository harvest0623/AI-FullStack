import { DynamicModule, Module } from '@nestjs/common';
import { ConfigService } from './config.service';
import { ConfigModuleOptions } from './config.interface';

/**
 * 动态模块 ConfigModule
 *
 * 对应官方 @nestjs/config 的最小化实现，演示动态模块的核心机制：
 *
 * 1. 类本身只用 @Module() 标注一个空壳
 * 2. 静态方法 forRoot(options) 在运行时返回一个 DynamicModule
 * 3. 返回值的 { module, providers, exports, global } 决定 Provider 如何注册
 *
 * 调用方式：
 *   ConfigModule.forRoot({ isGlobal: true })
 *
 * 与静态模块的区别：
 *   静态模块的 providers/exports 在编译期就写死；
 *   动态模块可以在运行时根据 options 生成不同的 providers，并决定是否注册为全局。
 */
@Module({})
export class ConfigModule {
  static forRoot(options: ConfigModuleOptions = {}): DynamicModule {
    // 在工厂里直接 new 出 ConfigService 实例，把 options 注入进去。
    // 真实库里通常用 useFactory + inject 形式以支持异步加载，这里为了演示逻辑做了简化。
    const configService = new ConfigService(options);

    return {
      module: ConfigModule,
      providers: [
        {
          provide: ConfigService,
          useValue: configService,
        },
      ],
      exports: [ConfigService],
      global: options.isGlobal ?? false,
    };
  }
}
