import { Module } from '@nestjs/common';
import { APP_PIPE } from '@nestjs/core';
import { ArticlesModule } from './articles/articles.module';
import { UsersModule } from './users/users.module';
import { TrimPipe } from './pipes/trim.pipe';

/**
 * 根模块
 *
 * 演示全局 Pipe 注册的第二种方式：APP_PIPE Provider。
 *
 * 与 main.ts 中的 app.useGlobalPipes() 不同，APP_PIPE 通过 NestJS 的 DI 容器实例化管道，
 * 因此管道的构造函数可以注入其他 Provider（如 ConfigService）。
 *
 * 这里注册 TrimPipe 为全局管道，对所有控制器的 @Body() 自动去除字符串两端空格。
 * 它与 main.ts 中的 ValidationPipe 共同工作：
 *   - ValidationPipe（useGlobalPipes）负责 DTO 校验
 *   - TrimPipe（APP_PIPE）负责字符串净化
 *
 * 注意：当 useGlobalPipes 与 APP_PIPE 同时存在时，二者的相对执行顺序由 NestJS 内部决定。
 * 如果对顺序有严格要求（例如必须先 trim 再 validate），建议把所有全局 Pipe 放在同一个注册位置。
 */
@Module({
  imports: [ArticlesModule, UsersModule],
  providers: [
    {
      provide: APP_PIPE,
      useClass: TrimPipe,
    },
  ],
})
export class AppModule {}
