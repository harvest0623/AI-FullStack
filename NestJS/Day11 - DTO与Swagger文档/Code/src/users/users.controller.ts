import {
  Body,
  Controller,
  Get,
  HttpCode,
  HttpStatus,
  Param,
  ParseIntPipe,
  Post,
} from '@nestjs/common';
import {
  ApiBearerAuth,
  ApiBody,
  ApiCreatedResponse,
  ApiNotFoundResponse,
  ApiOkResponse,
  ApiOperation,
  ApiParam,
  ApiTags,
} from '@nestjs/swagger';

import { UsersService } from './users.service';
import { CreateUserDto } from './dto/create-user.dto';
import { UserResponseDto } from './dto/user-response.dto';

/**
 * 用户控制器（第二个资源演示）
 *
 * 与 ArticlesController 的对照点：
 *   1. 同样使用 @ApiTags 归类到"用户"分组
 *   2. 同样使用 @ApiOperation / @ApiResponse 系列装饰器
 *   3. 重点演示"请求 DTO 有 password、响应 DTO 没 password"的契约设计
 *
 * 在 Swagger UI 里你将看到：
 *   - POST /users 的请求体包含 password 字段
 *   - POST /users 的 201 响应里没有 password 字段
 * 这就是"DTO 与 Entity 分离"的直观体现。
 */
@ApiTags('用户')
@ApiBearerAuth()
@Controller('users')
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Get()
  @ApiOperation({ summary: '获取全部用户' })
  @ApiOkResponse({
    description: '用户列表（不含密码）',
    type: [UserResponseDto],
  })
  findAll() {
    return this.usersService.findAll();
  }

  @Get(':id')
  @ApiOperation({ summary: '获取用户详情' })
  @ApiParam({ name: 'id', description: '用户 ID', example: 1 })
  @ApiOkResponse({
    description: '用户详情（不含密码）',
    type: UserResponseDto,
  })
  @ApiNotFoundResponse({ description: '用户不存在' })
  findOne(@Param('id', ParseIntPipe) id: number) {
    return this.usersService.findOne(id);
  }

  @Post()
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({
    summary: '创建用户',
    description: '请求体包含 password，但响应里不会返回 password。',
  })
  @ApiBody({ description: '用户注册信息', type: CreateUserDto })
  @ApiCreatedResponse({
    description: '创建成功（不含密码）',
    type: UserResponseDto,
  })
  create(@Body() dto: CreateUserDto) {
    return this.usersService.create(dto);
  }
}
