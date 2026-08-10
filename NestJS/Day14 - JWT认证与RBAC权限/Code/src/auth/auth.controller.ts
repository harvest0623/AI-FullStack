import {
  Body,
  Controller,
  Get,
  HttpCode,
  Post,
  Req,
  UseGuards,
} from '@nestjs/common';
import { Request } from 'express';
import { AuthService, TokenResponse } from './auth.service';
import { LocalAuthGuard } from './guards/local-auth.guard';
import { JwtAuthGuard } from './guards/jwt-auth.guard';
import { CurrentUser } from './decorators/current-user.decorator';
import { JwtPayload } from './strategies/jwt.strategy';
import { RegisterUserDto } from '../users/dto/register-user.dto';
import { LoginUserDto } from '../users/dto/login-user.dto';
import { SafeUser } from '../users/user.entity';
import { Roles } from '../common/decorators/roles.decorator';

/**
 * AuthController —— 认证授权接口入口
 *
 * 路由清单：
 *   POST /auth/register    公开：注册（bcrypt 哈希密码）
 *   POST /auth/login       公开：登录（LocalStrategy 校验 → 签发 JWT）
 *   GET  /auth/profile     需 JWT：返回当前登录用户
 *   POST /auth/refresh     公开：用 refresh token 换新 access token
 *   POST /auth/logout      需 JWT：把 access token 加入黑名单
 *   GET  /auth/admin-only  需 JWT + admin 角色：演示 RBAC
 *
 * 守卫组合策略：
 *   - register / refresh：公开，无需任何守卫
 *   - login：LocalAuthGuard（用账号密码换 token）
 *   - profile / logout：JwtAuthGuard（用 access token 访问）
 *   - admin-only：JwtAuthGuard（认证）+ 全局 RolesGuard（授权）
 *     注意 RolesGuard 是 AppModule 通过 APP_GUARD 注册的全局守卫，
 *     控制器只需 @Roles('admin') 声明即可，无需 @UseGuards(RolesGuard)。
 */
@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  /**
   * 注册：接收用户名 / 密码 / 可选角色，创建用户。
   * 密码哈希在 UsersService.create 中完成（bcrypt）。
   */
  @Post('register')
  async register(@Body() dto: RegisterUserDto): Promise<SafeUser> {
    return this.authService.signUp(dto);
  }

  /**
   * 登录：LocalAuthGuard 触发 LocalStrategy.validate，
   * 校验通过后 user 被挂到 req.user，这里直接交给 AuthService 签发 JWT。
   *
   * 注意 LoginUserDto 在路由上不显式 @Body() 标注，
   * 因为 LocalStrategy 直接从 req.body 读 username/password，
   * 但我们仍声明 @Body() dto: LoginUserDto 是为了让 ValidationPipe 校验请求体格式。
   * 校验通过后 dto 本身不会被使用（策略已读过）。
   */
  @UseGuards(LocalAuthGuard)
  @Post('login')
  @HttpCode(200) // 登录是查询语义，默认 201 不合适
  login(
    @Body() _dto: LoginUserDto,
    @CurrentUser() user: JwtPayload,
  ): Promise<TokenResponse> {
    return this.authService.login(user);
  }

  /**
   * 获取当前登录用户信息。
   * JwtAuthGuard 解析 token 后，user 已挂到 req.user，
   * @CurrentUser() 把它注入到参数。
   */
  @UseGuards(JwtAuthGuard)
  @Get('profile')
  profile(@CurrentUser() user: JwtPayload): JwtPayload {
    return user;
  }

  /**
   * 刷新 token：客户端在 access token 过期前，
   * 用 refresh token 换取新的 token 对。
   *
   * 这里不挂 JwtAuthGuard —— 因为 access token 可能已过期，
   * 入口不能依赖它。refresh token 的校验由 AuthService.refreshToken
   * 通过 JwtService.verifyAsync 完成。
   */
  @Post('refresh')
  @HttpCode(200)
  refresh(
    @Body('refresh_token') refreshToken: string,
  ): Promise<TokenResponse> {
    return this.authService.refreshToken(refreshToken);
  }

  /**
   * 登出：把当前 access token 加入黑名单。
   * 客户端配合清除本地存储的 access / refresh token。
   */
  @UseGuards(JwtAuthGuard)
  @Post('logout')
  @HttpCode(200)
  async logout(@Req() req: Request): Promise<{ message: string }> {
    const auth = req.headers.authorization ?? '';
    const token = auth.startsWith('Bearer ') ? auth.slice(7) : '';
    await this.authService.logout(token);
    return { message: '已登出' };
  }

  /**
   * 演示：JWT 认证 + RBAC 授权的组合。
   *
   * JwtAuthGuard 做认证（解析 token → req.user）
   * RolesGuard（全局）做授权（@Roles('admin') → 校验 req.user.roles）
   *
   * 二者通过 req.user 解耦：
   *   - JwtAuthGuard 不关心 roles，只负责身份
   *   - RolesGuard 不关心 token，只负责角色匹配
   */
  @UseGuards(JwtAuthGuard)
  @Roles('admin')
  @Get('admin-only')
  adminOnly(
    @CurrentUser() user: JwtPayload,
  ): { message: string; user: JwtPayload } {
    return { message: '只有 admin 角色能访问此接口', user };
  }
}
