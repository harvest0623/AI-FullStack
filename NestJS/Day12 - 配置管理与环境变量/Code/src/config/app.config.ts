import { registerAs } from '@nestjs/config';

/**
 * 应用层配置命名空间
 *
 * registerAs('app') 把返回值挂到 configService 的 'app' 命名空间下：
 *   configService.get('app.port')      -> 3000
 *   configService.get('app.name')      -> 'nest-day12-config-demo'
 *
 * 与直接写在 configuration.ts 里的区别：
 *   - 独立文件维护，模块边界清晰
 *   - 类型推断更准确（配合 ConfigType<typeof appConfig>）
 *   - 可按需 lazy 加载，不影响其他配置
 *
 * 命名空间字符串 'app' 必须与 config.interface.ts 中的字段名一致。
 */
export const appConfig = registerAs('app', () => ({
  name: process.env.APP_NAME || 'nest-app',
  port: parseInt(process.env.APP_PORT || '3000', 10),
  prefix: process.env.APP_PREFIX || 'api/v1',
  env: process.env.NODE_ENV || 'development',
}));

export type AppConfigType = typeof appConfig;
