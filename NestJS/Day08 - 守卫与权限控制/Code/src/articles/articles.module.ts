import { Module } from '@nestjs/common';
import { ArticlesController } from './articles.controller';

/**
 * 文章模块
 *
 * 本章聚焦守卫与权限控制，控制器内不依赖 Service，
 * 所有数据都用 mock 返回，因此模块只声明 controller。
 *
 * 全局守卫（AuthGuard / RolesGuard / PermissionGuard）通过
 * AppModule 的 APP_GUARD 注册，对当前模块的所有路由自动生效，
 * 这里不需要再单独 @UseGuards。
 */
@Module({
  controllers: [ArticlesController],
  providers: [],
})
export class ArticlesModule {}
