import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import {
  IsEmail,
  IsEnum,
  IsOptional,
  IsString,
  MinLength,
  MaxLength,
} from 'class-validator';

/**
 * 用户角色枚举
 *
 * 用 enum 而非字符串字面量，便于 Swagger 展示合法值，
 * 也避免调用方拼错字符串。
 */
export enum UserRole {
  ADMIN = 'admin',
  EDITOR = 'editor',
  READER = 'reader',
}

/**
 * 创建用户 DTO（请求契约）
 *
 * 这里特意演示"请求 DTO 与响应 DTO 字段不同"的场景：
 *   - 请求 DTO 包含 password（创建时需要传密码）
 *   - 响应 DTO 不包含 password（永远不返回密码）
 * 这种"输入有、输出无"的契约设计是 DTO 模式的核心价值。
 */
export class CreateUserDto {
  @ApiProperty({
    description: '登录用户名，3~30 字符',
    example: 'alice',
    minLength: 3,
    maxLength: 30,
  })
  @IsString()
  @MinLength(3, { message: '用户名至少 3 个字符' })
  @MaxLength(30, { message: '用户名最多 30 个字符' })
  username: string;

  @ApiProperty({
    description: '邮箱地址，需符合标准邮箱格式',
    example: 'alice@example.com',
  })
  @IsEmail({}, { message: '邮箱格式不正确' })
  email: string;

  @ApiProperty({
    description: '登录密码，6~50 字符。注意：该字段不会出现在响应中。',
    example: 'p@ssw0rd123',
    minLength: 6,
    maxLength: 50,
  })
  @IsString()
  @MinLength(6, { message: '密码至少 6 个字符' })
  @MaxLength(50, { message: '密码最多 50 个字符' })
  password: string;

  @ApiPropertyOptional({
    description: '用户角色，默认 reader',
    enum: UserRole,
    default: UserRole.READER,
    example: UserRole.READER,
  })
  @IsOptional()
  @IsEnum(UserRole, { message: 'role 必须是 admin / editor / reader 之一' })
  role?: UserRole = UserRole.READER;

  @ApiPropertyOptional({
    description: '昵称，可选',
    example: '小红',
  })
  @IsOptional()
  @IsString()
  nickname?: string;
}
