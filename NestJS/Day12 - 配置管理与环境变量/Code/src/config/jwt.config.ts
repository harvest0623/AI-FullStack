import { registerAs } from '@nestjs/config';

/**
 * JWT 配置命名空间
 *
 * registerAs('jwt') 创建 'jwt' 命名空间：
 *   configService.get('jwt.secret')         -> 'xxx'
 *   configService.get('jwt.expiresIn')      -> '1h'
 *
 * 安全提示：
 *   - JWT_SECRET 不能硬编码在代码里，必须来自环境变量
 *   - 生产环境至少 32 字符，建议用 openssl rand -hex 32 生成
 *   - secret 只在服务端使用，绝不下发给前端
 *
 * Day14 会用这里的字段签发与验证 JWT，本 Day 仅做读取演示。
 */
export const jwtConfig = registerAs('jwt', () => ({
  secret: process.env.JWT_SECRET || '',
  expiresIn: process.env.JWT_EXPIRES_IN || '1h',
  refreshExpiresIn: process.env.JWT_REFRESH_EXPIRES_IN || '7d',
}));

export type JwtConfigType = typeof jwtConfig;
