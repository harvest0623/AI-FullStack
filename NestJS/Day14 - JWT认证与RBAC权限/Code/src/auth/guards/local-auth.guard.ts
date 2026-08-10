import { Injectable } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';

/**
 * LocalAuthGuard —— 用户名密码登录守卫
 *
 * 极简封装：仅继承 AuthGuard('local')，触发 Passport 执行 LocalStrategy。
 *
 * 为什么不直接在控制器上 @UseGuards(AuthGuard('local'))？
 *   1. 命名更直观：LocalAuthGuard 一眼能看出是「本地登录守卫」
 *   2. 留扩展位：将来要加验证码、限流、IP 黑名单时只需改这个文件
 *   3. 与 JwtAuthGuard 形成对称命名，控制器读起来更整齐
 *
 * 用法：
 *   @UseGuards(LocalAuthGuard)
 *   @Post('login')
 *   login(@CurrentUser() user) { ... }
 *
 * 触发流程：
 *   LocalAuthGuard → Passport('local') → LocalStrategy.validate → req.user 挂载
 */
@Injectable()
export class LocalAuthGuard extends AuthGuard('local') {}
