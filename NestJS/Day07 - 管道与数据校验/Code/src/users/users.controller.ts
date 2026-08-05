import {
  Controller,
  Get,
  Param,
  Query,
  ParseIntPipe,
  ParseUUIDPipe,
  ParseEnumPipe,
  ParseFloatPipe,
  ParseBoolPipe,
  DefaultValuePipe,
} from '@nestjs/common';
import { CustomParseIntPipe } from '../pipes/parse-int.pipe';

/**
 * 用户角色枚举
 *
 * 用于演示 ParseEnumPipe：传入的 role 必须是该枚举的成员之一。
 */
export enum UserRole {
  ADMIN = 'admin',
  EDITOR = 'editor',
  VIEWER = 'viewer',
}

/**
 * 用户控制器
 *
 * 演示 Pipe 的参数级应用层级，覆盖全部内置参数转换 / 格式校验管道：
 *   - ParseIntPipe       GET /users/:id
 *   - ParseUUIDPipe      GET /users/uuid/:uuid
 *   - ParseEnumPipe      GET /users/role/:role
 *   - ParseFloatPipe     GET /users/score/:score
 *   - ParseBoolPipe      GET /users/active/:active
 *   - DefaultValuePipe   GET /users (query: page)
 *   - CustomParseIntPipe GET /users/custom/:id（自定义管道教学）
 *
 * 路由顺序：所有静态多段路由放在动态单段路由 :id 之前，避免被 :id 提前命中。
 */
@Controller('users')
export class UsersController {
  /**
   * GET /users?page=1
   *
   * DefaultValuePipe：当 page 查询参数缺失时返回默认值 1。
   * 不抛异常，只是兜底。
   */
  @Get()
  findAll(
    @Query('page', new DefaultValuePipe(1)) page: number,
    @Query('pageSize', new DefaultValuePipe(10)) pageSize: number,
  ) {
    return {
      message: '获取用户列表',
      page,
      pageSize,
      data: [
        { id: 1, name: '张三', email: 'zhangsan@example.com' },
        { id: 2, name: '李四', email: 'lisi@example.com' },
      ],
      total: 2,
    };
  }

  /**
   * GET /users/uuid/:uuid
   *
   * ParseUUIDPipe：校验路径参数是否为合法 UUID 格式（默认校验所有版本）。
   * 常用于数据库主键为 UUID 的场景。
   *
   * 合法：550e8400-e29b-41d4-a716-446655440000
   * 非法：not-a-uuid → 400 Bad Request
   */
  @Get('uuid/:uuid')
  findByUuid(@Param('uuid', ParseUUIDPipe) uuid: string) {
    return {
      message: '通过 UUID 获取用户',
      uuid,
      data: { id: uuid, name: 'UUID 用户', email: 'uuid@example.com' },
    };
  }

  /**
   * GET /users/role/:role
   *
   * ParseEnumPipe：校验路径参数是否为指定枚举的成员。
   * 传入实例方式：new ParseEnumPipe(UserRole)。
   *
   * 合法：admin / editor / viewer
   * 非法：superadmin → 400 Bad Request
   */
  @Get('role/:role')
  findByRole(
    @Param('role', new ParseEnumPipe(UserRole)) role: UserRole,
  ) {
    return {
      message: '按角色查询用户',
      role,
      data: { name: `角色为 ${role} 的用户` },
    };
  }

  /**
   * GET /users/score/:score
   *
   * ParseFloatPipe：把字符串路径参数转换成浮点数。
   *
   * 合法：3.14 / 95 / -0.5
   * 非法：abc → 400 Bad Request
   */
  @Get('score/:score')
  findByScore(@Param('score', ParseFloatPipe) score: number) {
    return {
      message: '按分数查询用户',
      score,
      data: { name: `分数为 ${score} 的用户` },
    };
  }

  /**
   * GET /users/active/:active
   *
   * ParseBoolPipe：把字符串转换成布尔值。
   * 支持的合法值：true / false / 1 / 0（不区分大小写）。
   *
   * 合法：true / TRUE / 1 / 0
   * 非法：yes → 400 Bad Request
   */
  @Get('active/:active')
  findByActive(@Param('active', ParseBoolPipe) active: boolean) {
    return {
      message: '按激活状态查询用户',
      active,
      data: { name: active ? '已激活用户' : '未激活用户' },
    };
  }

  /**
   * GET /users/custom/:id
   *
   * 使用自定义 CustomParseIntPipe（src/pipes/parse-int.pipe.ts）。
   * 与内置 ParseIntPipe 行为一致，但错误信息会带上参数名：
   *   "参数 "id" 必须是整数，但收到: "abc""
   *
   * 用于教学：理解 PipeTransform 接口的工作机制。
   */
  @Get('custom/:id')
  findByIdCustom(@Param('id', CustomParseIntPipe) id: number) {
    return {
      message: '通过自定义 ParseIntPipe 获取用户',
      id,
      data: { id, name: '自定义管道用户', email: 'custom@example.com' },
    };
  }

  /**
   * GET /users/:id
   *
   * 内置 ParseIntPipe：把字符串路径参数转换成整数。
   * 这是最常用的参数级管道，放在最后避免覆盖其他静态多段路由。
   *
   * 合法：123 / 0 / -5
   * 非法：abc → 400 Bad Request
   */
  @Get(':id')
  findOne(@Param('id', ParseIntPipe) id: number) {
    return {
      message: '获取用户详情',
      id,
      data: { id, name: '张三', email: 'zhangsan@example.com' },
    };
  }
}
