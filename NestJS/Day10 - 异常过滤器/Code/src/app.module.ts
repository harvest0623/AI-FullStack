import { Module } from '@nestjs/common';
import { APP_FILTER } from '@nestjs/core';
import { ArticlesModule } from './articles/articles.module';
import { AllExceptionsFilter } from './filters/all-exceptions.filter';
import { HttpExceptionFilter } from './filters/http-exception.filter';
import { BusinessExceptionFilter } from './filters/business-exception.filter';

/**
 * Day10 根模块
 *
 * 通过 APP_FILTER 令牌注册全局过滤器，三个过滤器分工：
 *   - AllExceptionsFilter  @Catch()             兜底所有未捕获异常（最外层）
 *   - HttpExceptionFilter  @Catch(HttpException) 捕获 NestJS 内置异常
 *   - BusinessExceptionFilter @Catch(BusinessException) 捕获业务异常（最内层）
 *
 * 注册顺序 = 过滤器洋葱模型的层叠顺序：
 *   先注册 = 外层（兜底）  后注册 = 内层（贴近 handler，优先匹配）
 *
 * 由于每个过滤器都用 @Catch 指定了具体异常类型，NestJS 会自动按类型分发：
 *   - BusinessException 实例只进 BusinessExceptionFilter
 *   - HttpException 实例只进 HttpExceptionFilter
 *   - 其他 Error 实例进 AllExceptionsFilter
 * 三者互不干扰，无需在 catch 里手动判断类型再 re-throw。
 *
 * APP_FILTER 相比 main.ts 中 useGlobalFilters 的优势：
 *   - 支持 DI，过滤器构造函数可以注入 Service、Config、Logger 等
 *   - 与模块系统一致，便于按模块隔离与测试
 */
@Module({
  imports: [ArticlesModule],
  providers: [
    // 最外层：兜底所有未捕获异常（@Catch() 无参数）
    { provide: APP_FILTER, useClass: AllExceptionsFilter },
    // 中间层：捕获 HttpException 及其子类
    { provide: APP_FILTER, useClass: HttpExceptionFilter },
    // 最内层：捕获自定义业务异常（最贴近 handler，优先处理）
    { provide: APP_FILTER, useClass: BusinessExceptionFilter },
  ],
})
export class AppModule {}
