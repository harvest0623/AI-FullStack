import {
  ExecutionContext,
  Injectable,
  UnauthorizedException,
} from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';
import { ExtractJwt } from 'passport-jwt';
import { AuthService } from '../auth.service';

/**
 * JwtAuthGuard —— JWT 认证守卫
 *
 * 这是 Day08 简化版 AuthGuard 的「正式版」替代：
 *   Day08：硬编码 token → user 映射，无签名校验，仅供演示守卫机制
 *   Day14：通过 Passport JwtStrategy 校验签名 + 过期，生产可用
 *
 * 工作流程：
 *   1. 从 Authorization: Bearer <token> 提取 token
 *   2. 黑名单校验（登出的 token 直接拒绝，无须走 Passport）
 *   3. 委托 super.canActivate() → Passport JwtStrategy
 *      - 校验签名（用 JWT_SECRET）
 *      - 校验过期时间
 *      - 调用 JwtStrategy.validate(payload) 把 user 挂到 req.user
 *   4. 全部通过 → 放行进入控制器
 *
 * 与全局 RolesGuard 的配合：
 *   - JwtAuthGuard 负责认证（你是谁）
 *   - RolesGuard 负责授权（你能做什么）
 *   - 两者通过 req.user 解耦，互不依赖
 *
 * 为什么要在 canActivate 里先查黑名单？
 *   - JwtStrategy.validate 拿到的是解码后的 payload，不是原始 token
 *   - 黑名单存的是原始 token 字符串，必须在策略校验前用请求头里的原始 token 比对
 *   - 提前拦截也省去了一次签名校验计算
 */
@Injectable()
export class JwtAuthGuard extends AuthGuard('jwt') {
  constructor(private readonly authService: AuthService) {
    super();
  }

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest();

    // ① 提取原始 token 做黑名单校验
    const token = ExtractJwt.fromAuthHeaderAsBearerToken()(request);
    if (token && this.authService.isBlacklisted(token)) {
      throw new UnauthorizedException('Token 已登出，请重新登录');
    }

    // ② 委托 Passport JwtStrategy 校验签名 + 过期 + 挂载 req.user
    return (await super.canActivate(context)) as boolean;
  }
}
