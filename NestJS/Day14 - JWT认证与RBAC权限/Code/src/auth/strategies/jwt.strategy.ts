import { Injectable, UnauthorizedException } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import { ExtractJwt, Strategy } from 'passport-jwt';
import { ConfigService } from '@nestjs/config';

/**
 * JwtPayload —— JWT 载荷结构
 *
 * 这是「签发」与「校验」两端共享的契约：
 *   - AuthService.generateTokens 把用户身份写入 payload
 *   - JwtStrategy.validate 拿到解码后的 payload，提取出 req.user
 *   - common/express.d.ts 把 Request.user 类型声明为 JwtPayload
 *
 * 字段说明：
 *   - sub：JWT 标准字段，subject，这里放用户 id
 *   - username / roles / permissions：业务身份信息
 *   - type：token 类型（'access' | 'refresh'），用于在策略层区分用途
 *
 * 为什么把 type 放进 payload 而不是用两个 secret？
 *   - 同一 secret 简化配置
 *   - 通过 type 字段在策略层显式校验，更易理解
 *   - 生产里若要更强隔离可用 useFactory 注册两个 JwtModule（access / refresh）
 */
export interface JwtPayload {
  /** 用户 id（JWT 标准 sub 字段） */
  sub: number;
  /** 登录用户名 */
  username: string;
  /** RBAC0 角色集合 */
  roles: string[];
  /** RBAC0 权限集合 */
  permissions: string[];
  /** token 类型，区分 access / refresh */
  type?: 'access' | 'refresh';
}

/**
 * JwtStrategy —— JWT 校验策略
 *
 * 工作原理：
 *   1. passport-jwt 通过 jwtFromRequest 从请求头 Authorization: Bearer <token> 提取 token
 *   2. 用 secretOrKey 校验签名 + 过期时间
 *   3. 校验通过后把解码的 payload 传给 validate(payload)
 *   4. validate 的返回值会被 Passport 挂到 req.user，供后续守卫 / 控制器使用
 *
 * 与 LocalStrategy 的对比：
 *   - LocalStrategy：校验账号密码，验证「你是谁」（认证）
 *   - JwtStrategy：校验 token 签名，验证「你持有合法凭证」（认证延续）
 *
 * 为什么 validate 只返回部分字段而不是直接 return payload？
 *   - 显式白名单可以避免把过期时间、iat 等内部字段污染 req.user
 *   - 防御性编程：万一 payload 被注入未预期字段，不会透传到下游
 */
@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy, 'jwt') {
  constructor(private readonly configService: ConfigService) {
    super({
      // 从 Authorization: Bearer <token> 提取 token
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
      // false = 校验过期时间，过期的 token 直接 401
      ignoreExpiration: false,
      // 签名密钥，与签发端保持一致（来自 .env 的 JWT_SECRET）
      secretOrKey:
        configService.get<string>('JWT_SECRET') ?? 'insecure-default-secret',
    });
  }

  /**
   * Passport 在签名 + 过期校验通过后调用此方法。
   * 返回值会被挂到 req.user。
   */
  async validate(payload: JwtPayload): Promise<JwtPayload> {
    // 仅允许 access token 访问受保护资源
    // refresh token 只能用于 /auth/refresh，由 AuthService.refreshToken 单独校验
    if (payload.type && payload.type !== 'access') {
      throw new UnauthorizedException('请使用 access token 访问受保护资源');
    }

    // 显式挑选字段，构造 req.user
    return {
      sub: payload.sub,
      username: payload.username,
      roles: payload.roles,
      permissions: payload.permissions,
      type: payload.type,
    };
  }
}
