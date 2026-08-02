import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';

/**
 * 根模块
 *
 * 整个 NestJS 应用只有一个根模块，被 main.ts 的 NestFactory.create() 消费。
 * 所有特性模块（如 UserModule、ArticleModule）通过 imports 字段挂载到根模块，
 * 形成模块树。DI 容器会沿着这棵树解析依赖。
 *
 * @Module 装饰器接收的四个核心字段：
 *   - imports    引入其他模块，获取它们 exports 出的 Provider
 *   - controllers 注册本模块的控制器，NestJS 会自动实例化并绑定路由
 *   - providers  注册本模块的 Provider（Service / Repository / Value / Factory）
 *   - exports    把本模块的 Provider 暴露给其他模块使用
 */
@Module({
  imports: [],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
