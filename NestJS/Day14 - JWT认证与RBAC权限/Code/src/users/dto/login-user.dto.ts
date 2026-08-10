import { IsString, MinLength, MaxLength } from 'class-validator';

/**
 * 登录请求 DTO
 *
 * 仅含 username + password，由 LocalStrategy 读取后调用 AuthService.validateUser 校验。
 * 登录请求不应携带 roles / permissions 等敏感字段——
 * 这些字段只能由服务端在认证通过后从用户记录里读取，并写入 JWT。
 */
export class LoginUserDto {
  @IsString()
  @MinLength(3, { message: '用户名至少 3 个字符' })
  @MaxLength(20, { message: '用户名至多 20 个字符' })
  username!: string;

  @IsString()
  @MinLength(6, { message: '密码至少 6 个字符' })
  @MaxLength(32, { message: '密码至多 32 个字符' })
  password!: string;
}
