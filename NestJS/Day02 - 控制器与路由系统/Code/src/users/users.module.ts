import { Module } from '@nestjs/common';
import { UsersController } from './users.controller';

/**
 * 用户模块
 *
 * 与 ArticlesModule 类似，
 * Day02 阶段仅注册控制器，
 * Day04 引入 Provider 后会补充 UsersService。
 */
@Module({
  controllers: [UsersController],
  providers: [],
})
export class UsersModule {}
