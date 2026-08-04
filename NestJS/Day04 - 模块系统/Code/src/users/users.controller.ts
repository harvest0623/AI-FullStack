import { Controller, Get, Param, ParseIntPipe } from '@nestjs/common';
import { UsersService } from './users.service';

@Controller('users')
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Get()
  findAll() {
    return this.usersService.findAll();
  }

  /**
   * 演示跨模块调用：返回某用户及其文章
   * GET /users/1/articles
   */
  @Get(':id/articles')
  findUserWithArticles(@Param('id', ParseIntPipe) id: number) {
    return this.usersService.findUserWithArticles(id);
  }
}
