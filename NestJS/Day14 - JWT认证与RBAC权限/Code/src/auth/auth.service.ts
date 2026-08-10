import {
  Injectable,
  UnauthorizedException,
  NotFoundException,
} from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import { UsersService } from '../users/users.service';
import { RegisterUserDto } from '../users/dto/register-user.dto';
import { SafeUser } from '../users/user.entity';
import { JwtPayload } from './strategies/jwt.strategy';

/**
 * Token 响应结构（登录 / 刷新接口的返回值）
 *
 * 遵循 OAuth2 标准字段命名：
 *   - access_token：短期凭证，访问受保护资源时放 Authorization: Bearer <access_token>
 *   - refresh_token：长期凭证，仅用于换取新 access_token，不应放 URL / 日志
 *   - token_type：固定 'Bearer'
 *   - expires_in：access_token 过期秒数，前端据此提前刷新
 */
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'Bearer';
  expires_in: number;
}

/**
 * AuthService —— 认证领域服务
 *
 * 职责：
 *   1. signUp：注册（委托 UsersService.create 做密码哈希 + 入库）
 *   2. validateUser：账号密码校验（供 LocalStrategy 调用）
 *   3. login / generateTokens：签发 access + refresh token
 *   4. refreshToken：用 refresh token 换新 access token
 *   5. logout：把 token 加入黑名单
 *
 * 与 Day08 的对比：
 *   Day08 的「认证」是硬编码 token → user 映射，无任何密码校验。
 *   本章用 bcrypt 校验密码、用 JWT 签发凭证，是真实生产可用的最小实现。
 */
@Injectable()
export class AuthService {
  /**
   * Token 黑名单（演示用，进程内存）
   *
   * 局限：
   *   - 多实例部署时不共享（实例 A 登出，实例 B 仍认）
   *   - 进程重启后清空
   *   - 不会自动过期，长时间运行会膨胀
   *
   * 生产实践：
   *   用 Redis SET + EXPIRE 实现，TTL = token 剩余有效期；
   *   或采用「短 access token + 长 refresh token + 服务端撤销列表」的组合。
   */
  private readonly blacklist = new Set<string>();

  constructor(
    private readonly usersService: UsersService,
    private readonly jwtService: JwtService,
    private readonly configService: ConfigService,
  ) {}

  /** 注册：委托 UsersService 创建用户（含 bcrypt 哈希） */
  async signUp(dto: RegisterUserDto): Promise<SafeUser> {
    return this.usersService.create(dto);
  }

  /**
   * 校验账号密码（供 LocalStrategy 调用）。
   *
   * 返回值是「不含 type 字段」的 JwtPayload，
   * 因为这里只是确认身份，token 类型由 generateTokens 决定。
   *
   * @returns 校验通过返回 JwtPayload；失败返回 null（由 LocalStrategy 抛 401）
   */
  async validateUser(
    username: string,
    password: string,
  ): Promise<JwtPayload | null> {
    const user = this.usersService.findByUsername(username);
    if (!user) {
      // 故意返回 null 而非区分「用户不存在 / 密码错误」，
      // 避免给攻击者枚举用户名的信号
      return null;
    }

    const valid = await this.usersService.validatePassword(
      password,
      user.password,
    );
    if (!valid) {
      return null;
    }

    return {
      sub: user.id,
      username: user.username,
      roles: user.roles,
      permissions: user.permissions,
    };
  }

  /** 登录：校验通过后签发 token 对 */
  async login(user: JwtPayload): Promise<TokenResponse> {
    return this.generateTokens(user);
  }

  /**
   * 签发 access + refresh token 对。
   *
   * access token 短期（15m）：放在内存里，被受保护接口校验
   * refresh token 长期（7d）：放 httpOnly cookie / 安全存储，仅用于 /auth/refresh
   *
   * 为什么不直接签一个超长 access token？
   *   - access token 一旦泄露，攻击者可在有效期内任意冒用
   *   - 短 access token 限制暴露窗口，长 refresh token 让用户不必频繁输密码
   *   - refresh token 只走 /auth/refresh 一个端点，便于做风控（频率、IP 校验）
   */
  async generateTokens(payload: JwtPayload): Promise<TokenResponse> {
    const expiresIn =
      this.configService.get<string>('JWT_EXPIRES_IN') ?? '15m';
    const refreshExpiresIn =
      this.configService.get<string>('JWT_REFRESH_EXPIRES_IN') ?? '7d';

    const access_token = this.jwtService.sign(
      { ...payload, type: 'access' as const },
      { expiresIn },
    );
    const refresh_token = this.jwtService.sign(
      { ...payload, type: 'refresh' as const },
      { expiresIn: refreshExpiresIn },
    );

    return {
      access_token,
      refresh_token,
      token_type: 'Bearer',
      expires_in: this.parseExpiresToSeconds(expiresIn),
    };
  }

  /**
   * 用 refresh token 换新 token 对。
   *
   * 关键点：
   *   1. 用 verifyAsync 校验签名 + 过期
   *   2. 校验 type === 'refresh'，防止 access token 也来刷新
   *   3. 校验黑名单（已登出的 refresh token 不可复用）
   *   4. 重新查 DB 拿最新角色权限，避免 token 签发后被撤销权限仍生效
   *
   * 为什么不直接信任 payload 里的 roles？
   *   若用户在 refresh token 有效期内被撤销了 admin 角色，
   *   直接用 payload 会让他继续以 admin 身份操作 7 天，这是严重的安全漏洞。
   *   所以必须每次 refresh 都重新读 DB。
   */
  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    let payload: JwtPayload;
    try {
      payload = await this.jwtService.verifyAsync<JwtPayload>(refreshToken);
    } catch {
      throw new UnauthorizedException('refresh token 无效或已过期');
    }

    if (payload.type !== 'refresh') {
      throw new UnauthorizedException('请使用 refresh token 刷新');
    }

    if (this.isBlacklisted(refreshToken)) {
      throw new UnauthorizedException('refresh token 已登出，请重新登录');
    }

    // 重新读取用户最新身份
    const user = this.usersService.findById(payload.sub);
    if (!user) {
      throw new NotFoundException('用户已被删除，无法刷新');
    }

    return this.generateTokens({
      sub: user.id,
      username: user.username,
      roles: user.roles,
      permissions: user.permissions,
    });
  }

  /**
   * 登出：把 token 加入黑名单。
   *
   * 由于 JWT 是无状态的，签发后服务端无法「撤销」一个未过期 token，
   * 只能通过维护黑名单拒绝已登出的 token。
   *
   * 客户端配合：登出时同时清除本地存储的 access / refresh token。
   */
  async logout(token: string): Promise<void> {
    if (token) {
      this.blacklist.add(token);
    }
  }

  /** 判断 token 是否在黑名单中（供 JwtAuthGuard 调用） */
  isBlacklisted(token: string): boolean {
    return this.blacklist.has(token);
  }

  /** 把 '15m' / '7d' / '3600s' 这类字符串解析为秒数，供前端展示倒计时 */
  private parseExpiresToSeconds(expires: string): number {
    const match = /^(\d+)([smhd])$/.exec(expires);
    if (!match) return 900; // 默认 15 分钟
    const num = parseInt(match[1], 10);
    const unit = match[2];
    switch (unit) {
      case 's':
        return num;
      case 'm':
        return num * 60;
      case 'h':
        return num * 3600;
      case 'd':
        return num * 86400;
      default:
        return 900;
    }
  }
}
