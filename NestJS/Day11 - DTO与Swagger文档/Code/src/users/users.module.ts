import { Module } from '@nestjs/common';
import { UsersController } from './users.controller';
import { UsersService } from './users.service';

/**
 * 用户模块
 */
@Module({
  controllers: [UsersController],
  providers: [UsersService],
})
export class UsersModule {}
