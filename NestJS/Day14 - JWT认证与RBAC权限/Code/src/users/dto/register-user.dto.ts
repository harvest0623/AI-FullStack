import { IsString, MinLength, MaxLength, IsOptional, IsArray, ArrayUnique } from 'class-validator';

/**
 * 注册请求 DTO
 *
 * 配合全局 ValidationPipe 使用：
 *   - username：3 ~ 20 字符，避免过短用户名被暴力枚举
 *   - password：6 ~ 32 字符，最低门槛，真实项目应再叠加复杂度规则
 *   - roles：可选，未传时默认 ['visitor']，由 service 兜底
 *
 * 注意：DTO 只做格式校验，业务规则（用户名是否已存在）放在 service 层判断。
 */
export class RegisterUserDto {
  @IsString()
  @MinLength(3, { message: '用户名至少 3 个字符' })
  @MaxLength(20, { message: '用户名至多 20 个字符' })
  username!: string;

  @IsString()
  @MinLength(6, { message: '密码至少 6 个字符' })
  @MaxLength(32, { message: '密码至多 32 个字符' })
  password!: string;

  @IsOptional()
  @IsArray()
  @ArrayUnique({ message: '角色不能重复' })
  @IsString({ each: true })
  roles?: string[];
}
