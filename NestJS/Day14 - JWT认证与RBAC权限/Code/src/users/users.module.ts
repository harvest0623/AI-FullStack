import { Module } from '@nestjs/common';
import { UsersService } from './users.service';

/**
 * UsersModule —— 用户领域模块
 *
 * 仅导出 UsersService，供 AuthModule 注入使用。
 * 用户实体、DTO 是纯类型，不需要在 providers 里声明。
 *
 * 真实项目里本模块还会包含 UsersController（用户管理 CRUD）、
 * TypeORM forFeature([UserRepository]) 等。本章聚焦认证，省略管理接口。
 */
@Module({
  providers: [UsersService],
  exports: [UsersService],
})
export class UsersModule {}
