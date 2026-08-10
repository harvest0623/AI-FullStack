import { ExecutionContext, createParamDecorator } from '@nestjs/common';
import { JwtPayload } from '../strategies/jwt.strategy';

/**
 * @CurrentUser() —— 参数装饰器，从 req.user 提取当前登录用户
 *
 * 等价于在控制器里写 `@Req() req` 然后访问 `req.user`，
 * 但更精准：只取需要的字段，且类型安全。
 *
 * 设计动机：
 *   - 控制器不应该直接依赖 Express Request 对象（与框架解耦）
 *   - 显式声明需要 user 的哪个字段，便于阅读与单测
 *   - 配合 common/express.d.ts 的类型扩展，TS 能正确推导
 *
 * 用法：
 *   @Get('profile')
 *   @UseGuards(JwtAuthGuard)
 *   profile(@CurrentUser() user: JwtPayload) { return user; }
 *
 *   @Get('me/id')
 *   @UseGuards(JwtAuthGuard)
 *   myId(@CurrentUser('sub') id: number) { return { id }; }
 *
 * 工作原理：
 *   createParamDecorator 的回调接收 (data, ctx)：
 *     - data：装饰器传入的参数，如 'sub'，可空
 *     - ctx：ExecutionContext，用于切换到 HTTP 拿 request
 *   返回值就是被装饰参数的最终值
 */
export const CurrentUser = createParamDecorator(
  (
    data: keyof JwtPayload | undefined,
    ctx: ExecutionContext,
  ): JwtPayload | unknown => {
    const request = ctx.switchToHttp().getRequest();
    const user = request.user as JwtPayload | undefined;

    if (!user) {
      // 理论上 JwtAuthGuard / LocalAuthGuard 已挂载 user
      // 这里防御性返回 undefined，由控制器层决定如何处理
      return undefined;
    }

    // data 有值 → 只取该字段；data 为空 → 返回整个 user
    return data ? user[data] : user;
  },
);
