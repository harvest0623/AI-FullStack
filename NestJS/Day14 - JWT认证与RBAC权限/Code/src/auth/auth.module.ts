import { Module } from '@nestjs/common';
import { JwtModule } from '@nestjs/jwt';
import { PassportModule } from '@nestjs/passport';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { AuthController } from './auth.controller';
import { AuthService } from './auth.service';
import { LocalStrategy } from './strategies/local.strategy';
import { JwtStrategy } from './strategies/jwt.strategy';
import { UsersModule } from '../users/users.module';

/**
 * AuthModule —— 认证授权领域模块
 *
 * 装配关系：
 *   UsersModule   提供用户 CRUD（含 bcrypt 哈希）
 *   PassportModule 注册 Passport，让 @nestjs/passport 能注入策略
 *   JwtModule     提供 JwtService，用于 sign / verify
 *   LocalStrategy / JwtStrategy 两个策略 Provider
 *   AuthService   业务逻辑（signUp / validateUser / generateTokens / refresh / logout）
 *   AuthController 路由入口
 *
 * JwtModule.registerAsync vs register：
 *   - register({ secret, signOptions }) 是同步注册，
 *     要求在模块定义时就拿到 secret，但 secret 来自 .env，
 *     必须通过 ConfigService 异步读取，故用 registerAsync。
 *   - registerAsync 的 useFactory 接收 ConfigService，
 *     工厂返回的配置对象就是 JwtModule 的入参。
 *
 * 为什么 imports 里要再写一遍 ConfigModule？
 *   ConfigModule 在 AppModule 已用 isGlobal: true 注册，
 *   理论上全局可见。这里显式 import 是为了 useFactory 的依赖注入可见性，
 *   避免某些边界场景下 ConfigService 未注入（Nest 在动态模块中行为更稳妥）。
 */
@Module({
  imports: [
    UsersModule,
    PassportModule,
    JwtModule.registerAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (configService: ConfigService) => ({
        // 签名密钥：必须与 JwtStrategy 的 secretOrKey 一致
        secret:
          configService.get<string>('JWT_SECRET') ?? 'insecure-default-secret',
        // 默认签发选项（可在 sign() 时覆盖）
        signOptions: {
          expiresIn: configService.get<string>('JWT_EXPIRES_IN') ?? '15m',
        },
      }),
    }),
  ],
  controllers: [AuthController],
  providers: [AuthService, LocalStrategy, JwtStrategy],
  exports: [AuthService],
})
export class AuthModule {}
