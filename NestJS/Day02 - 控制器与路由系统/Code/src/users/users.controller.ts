import {
  Controller,
  Get,
  Post,
  Put,
  Patch,
  Delete,
  Param,
  Body,
  Query,
  HttpCode,
  HttpStatus,
} from '@nestjs/common';

/**
 * 用户控制器
 *
 * 演示标准 RESTful CRUD 设计：
 * - GET    /users        获取用户列表
 * - GET    /users/:id    获取用户详情
 * - POST   /users        创建用户
 * - PUT    /users/:id    全量更新用户
 * - PATCH  /users/:id    部分更新用户
 * - DELETE /users/:id    删除用户
 *
 * 为了对比 ArticlesController 全量演示装饰器的写法，
 * 这里只保留标准 CRUD，强调“控制器薄”的设计原则：
 * 控制器只负责路由与 DTO 映射，业务逻辑下沉到 Service（Day04 引入）。
 */
@Controller('users')
export class UsersController {
  /**
   * GET /users?page=1&pageSize=10
   */
  @Get()
  findAll(@Query('page') page = '1', @Query('pageSize') pageSize = '10') {
    return {
      message: '获取用户列表',
      page: Number(page),
      pageSize: Number(pageSize),
      data: [
        { id: 1, name: '张三', email: 'zhangsan@example.com' },
        { id: 2, name: '李四', email: 'lisi@example.com' },
      ],
      total: 2,
    };
  }

  /**
   * GET /users/:id
   * HttpStatus 枚举提供语义化的状态码常量。
   */
  @Get(':id')
  findOne(@Param('id') id: string) {
    return {
      message: '获取用户详情',
      id: Number(id),
      data: { id: Number(id), name: '张三', email: 'zhangsan@example.com' },
    };
  }

  /**
   * POST /users
   * 默认 201，配合 @HttpCode 也可改写。
   */
  @Post()
  @HttpCode(HttpStatus.CREATED)
  create(@Body() body: { name: string; email: string }) {
    return {
      message: '创建用户成功',
      data: { id: Math.floor(Math.random() * 1000) + 1, ...body },
    };
  }

  /**
   * PUT /users/:id
   */
  @Put(':id')
  update(@Param('id') id: string, @Body() body: { name: string; email: string }) {
    return {
      message: `PUT 全量更新用户 ${id}`,
      id: Number(id),
      data: body,
    };
  }

  /**
   * PATCH /users/:id
   */
  @Patch(':id')
  partialUpdate(@Param('id') id: string, @Body() body: Partial<{ name: string; email: string }>) {
    return {
      message: `PATCH 部分更新用户 ${id}`,
      id: Number(id),
      data: body,
    };
  }

  /**
   * DELETE /users/:id
   */
  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  remove(@Param('id') id: string) {
    return;
  }
}
