import { Module } from '@nestjs/common';
import { UsersController } from './users.controller';

/**
 * 用户模块
 *
 * Day07 聚焦管道与校验，providers 为空数组。
 * 控制器中使用的 ParseIntPipe / ParseUUIDPipe / ParseEnumPipe 等都是参数级管道，
 * 直接在装饰器中传入，不需要在模块中注册。
 */
@Module({
  controllers: [UsersController],
  providers: [],
})
export class UsersModule {}
