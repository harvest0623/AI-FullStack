import { ApiProperty } from '@nestjs/swagger';
import { OmitType } from '@nestjs/mapped-types';

import { CreateUserDto, UserRole } from './create-user.dto';

/**
 * 用户响应 DTO
 *
 * OmitType(CreateUserDto, ['password']) 的作用：
 *   以 CreateUserDto 为基础，剔除 password 字段，得到一个新类。
 *   派生类自动继承所有装饰器（class-validator + Swagger）。
 *
 * 这就是"响应 DTO 隐藏敏感字段"的标准做法：
 *   - Entity 里 password 字段必须存在（数据库要存）
 *   - 请求 DTO 里有 password（创建/登录时要传）
 *   - 响应 DTO 里 OmitType 剔除 password（永远不返回）
 *
 * 实际项目里通常会基于 Entity 派生 ResponseDto，而非基于 CreateUserDto。
 * 但本项目用内存数据演示没有真正的 Entity，所以从 CreateUserDto 派生。
 */
export class UserResponseDto extends OmitType(CreateUserDto, [
  'password',
] as const) {
  @ApiProperty({
    description: '用户 ID',
    example: 1,
  })
  id: number;

  @ApiProperty({
    description: '用户角色',
    enum: UserRole,
    example: UserRole.READER,
  })
  role: UserRole;

  @ApiProperty({
    description: '创建时间',
    example: '2025-07-26T08:00:00.000Z',
  })
  createdAt: string;
}
