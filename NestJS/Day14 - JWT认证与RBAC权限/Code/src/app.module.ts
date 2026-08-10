import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { APP_GUARD } from '@nestjs/core';
import { AuthModule } from './auth/auth.module';
import { UsersModule } from './users/users.module';
import { RolesGuard } from './common/roles.guard';

/**
 * Day14 根模块
 *
 * 装配关系：
 *   ConfigModule   全局环境变量（JWT_SECRET、过期时间等）
 *   UsersModule    用户 CRUD + bcrypt 密码哈希（内存模拟数据库）
 *   AuthModule     认证模块（LocalStrategy / JwtStrategy / JwtModule / Controller / Service）
 *
 * 全局守卫：
 *   这里仅注册 RolesGuard 作为「授权层」全局守卫。
 *   认证层（JwtAuthGuard / LocalAuthGuard）通过 @UseGuards 在控制器方法上显式声明，
 *   因为不同接口对认证方式的需求不同（login 走 local，profile 走 jwt），
 *   不适合一刀切注册成全局守卫。
 *
 * 与 Day08 的衔接：
 *   Day08 的 AuthGuard 是简化版（硬编码 token 映射），本章用 JwtAuthGuard 完整替代；
 *   RolesGuard 直接复用 Day08 实现，仅在「读取 req.user」的形状上对齐 JWT payload。
 */
@Module({
  imports: [
    // 全局注入 .env，使 JwtModule.registerAsync 能通过 ConfigService 读取 JWT_SECRET
    ConfigModule.forRoot({ isGlobal: true }),
    UsersModule,
    AuthModule,
  ],
  controllers: [],
  providers: [
    // 全局授权守卫：路由上标了 @Roles 才会校验，没标则放行
    { provide: APP_GUARD, useClass: RolesGuard },
  ],
})
export class AppModule {}
