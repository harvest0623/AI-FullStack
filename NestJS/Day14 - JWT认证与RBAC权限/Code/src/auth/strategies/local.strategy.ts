import { Injectable, UnauthorizedException } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import { Strategy } from 'passport-local';
import { AuthService } from '../auth.service';
import { JwtPayload } from './jwt.strategy';

/**
 * LocalStrategy —— 用户名密码登录策略
 *
 * 「Local」指「本地校验」，相对于 OAuth / SAML / OpenID 等第三方身份提供者。
 * 它从请求体读 username + password，交给 AuthService.validateUser 校验。
 *
 * Passport 策略模式：
 *   - Passport 是 Node 生态最流行的认证中间件库
 *   - 通过「策略」抽象不同认证方式：local、jwt、google、github、oauth2...
 *   - @nestjs/passport 把 Passport 包装成 Nest 风格的 Provider
 *
 * 工作流程（结合 /auth/login）：
 *   1. 请求进入 LocalAuthGuard（@UseGuards(LocalAuthGuard)）
 *   2. LocalAuthGuard 触发 Passport 执行 LocalStrategy
 *   3. LocalStrategy.validate(username, password) 被调用
 *   4. validate 内部委托 AuthService.validateUser 校验账号密码
 *   5. 校验通过 → 返回 user，Passport 把它挂到 req.user
 *      校验失败 → 抛 UnauthorizedException → 401
 *   6. LocalAuthGuard 放行，控制器方法继续执行
 *
 * super() 配置项：
 *   - 默认从 req.body.username / req.body.password 读取
 *   - 若想改字段名：super({ usernameField: 'email', passwordField: 'pwd' })
 *   - 若想用 session：super({ session: true })（本章用 JWT，不需要 session）
 */
@Injectable()
export class LocalStrategy extends PassportStrategy(Strategy, 'local') {
  constructor(private readonly authService: AuthService) {
    super();
  }

  /**
   * Passport 调用此方法做实际校验。
   * @param username 从 req.body.username 取
   * @param password 从 req.body.password 取
   * @returns 校验通过返回 JwtPayload，会被挂到 req.user
   * @throws UnauthorizedException 校验失败
   */
  async validate(username: string, password: string): Promise<JwtPayload> {
    const user = await this.authService.validateUser(username, password);
    if (!user) {
      // 不区分「用户不存在」与「密码错误」，避免用户名枚举攻击
      throw new UnauthorizedException('用户名或密码错误');
    }
    return user;
  }
}
