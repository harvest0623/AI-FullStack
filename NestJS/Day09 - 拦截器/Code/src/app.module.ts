import { Module } from '@nestjs/common';
import { APP_INTERCEPTOR } from '@nestjs/core';
import { ArticlesModule } from './articles/articles.module';
import { TransformInterceptor } from './interceptors/transform.interceptor';
import { TimeoutInterceptor } from './interceptors/timeout.interceptor';
import { ErrorInterceptor } from './interceptors/error.interceptor';

@Module({
  imports: [ArticlesModule],
  providers: [
    // 全局拦截器注册方式二：通过 APP_INTERCEPTOR token 注册
    // 优势：完全支持依赖注入（DI），拦截器可注入任意 Service
    // 多个全局拦截器按注册顺序执行：先注册的先进入 before 阶段
    { provide: APP_INTERCEPTOR, useClass: TransformInterceptor },
    { provide: APP_INTERCEPTOR, useClass: TimeoutInterceptor },
    { provide: APP_INTERCEPTOR, useClass: ErrorInterceptor },
  ],
})
export class AppModule {}
