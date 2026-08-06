import { Module } from '@nestjs/common';
import { APP_GUARD } from '@nestjs/core';
import { ArticlesModule } from './articles/articles.module';
import { AuthGuard } from './guards/auth.guard';
import { RolesGuard } from './guards/roles.guard';
import { PermissionGuard } from './guards/permission.guard';

/**
 * Day08 根模块
 *
 * 通过 APP_GUARD 把三个守卫注册成「全局守卫」：
 *   APP_GUARD → AuthGuard         认证层（解析 token → req.user）
 *   APP_GUARD → RolesGuard        角色层（@Roles 粗粒度）
 *   APP_GUARD → PermissionGuard   权限层（@Permissions 细粒度）
 *
 * 为什么用 APP_GUARD 而不是 app.useGlobalGuards？
 *   - useGlobalGuards 在 main.ts 中调用，守卫实例由我们手动 new，
 *     无法注入 Reflector / 其他 Provider，丧失 DI 能力。
 *   - APP_GUARD 是 Provider 注册，Nest 会通过 DI 容器创建守卫实例，
 *     自动注入 Reflector，且支持作用域、依赖链。
 *   - 生产项目一律推荐 APP_GUARD。
 *
 * 执行顺序：
 *   APP_GUARD 注册顺序 = 守卫执行顺序（先注册先执行）
 *   → AuthGuard → RolesGuard → PermissionGuard → 拦截器 → 控制器
 *
 * 为什么这么分三层而不是一个守卫写完？
 *   - 单一职责：改认证逻辑不会动授权逻辑
 *   - 可替换：将来 JWT 替换 mock token 只动 AuthGuard
 *   - 可测试：每个守卫独立单测，不耦合
 */
@Module({
  imports: [ArticlesModule],
  controllers: [],
  providers: [
    // 注册顺序即执行顺序
    { provide: APP_GUARD, useClass: AuthGuard },
    { provide: APP_GUARD, useClass: RolesGuard },
    { provide: APP_GUARD, useClass: PermissionGuard },
  ],
})
export class AppModule {}
