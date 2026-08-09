import 'reflect-metadata';
import { NestFactory } from '@nestjs/core';
import { Logger, ValidationPipe } from '@nestjs/common';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';

import { AppModule } from './app.module';

/**
 * Day11 启动入口
 *
 * 本文件演示 Swagger 文档的完整集成：
 *   1. DocumentBuilder 构建 OpenAPI 文档元信息（标题/版本/描述/认证）
 *   2. SwaggerModule.createDocument 基于 AppModule 扫描所有控制器与 DTO，
 *      生成 OpenAPI 3.0 JSON
 *   3. SwaggerModule.setup 挂载 Swagger UI 到 /api-docs 路径
 *
 * 启动后访问 http://localhost:3000/api-docs 即可看到交互式 API 文档。
 *
 * 工作原理简述：
 *   - NestJS 启动时会为每个控制器/DTO 收集装饰器元数据（reflect-metadata）
 *   - SwaggerModule.createDocument 读取这些元数据，按 OpenAPI 3 规范组装 JSON
 *   - setup 把这个 JSON 挂到 /api-docs-json（原始 JSON），并挂上 Swagger UI
 */
async function bootstrap() {
  const logger = new Logger('Bootstrap');
  const app = await NestFactory.create(AppModule);

  // 全局路由前缀
  app.setGlobalPrefix('api/v1');

  // 全局校验管道（呼应 Day07）：
  //   - whitelist：剥离 DTO 上没有装饰器的多余字段
  //   - forbidNonWhitelisted：多余字段直接报 400
  //   - transform：把 @Body() 转成 DTO 实例，@Query/@Param 按类型自动转换
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
      transformOptions: { enableImplicitConversion: true },
    }),
  );

  app.enableCors();

  // ============ Swagger 文档配置 ============
  // DocumentBuilder 采用链式 API 构建 OpenAPI 文档元信息
  const config = new DocumentBuilder()
    .setTitle('Day11 - DTO 与 Swagger 文档 Demo')
    .setDescription(
      [
        '演示如何用 DTO + @nestjs/swagger 自动生成交互式 API 文档。',
        '',
        '## 学习重点',
        '- 请求 DTO 与响应 DTO 的分离',
        '- @nestjs/mapped-types 派生（PartialType / OmitType / PickType / IntersectionType）',
        '- Swagger 装饰器：@ApiTags / @ApiOperation / @ApiResponse / @ApiProperty',
        '- Bearer Token 认证配置',
        '',
        '## 试用流程',
        '1. 点击任意接口展开',
        '2. 点击 "Try it out" 按钮',
        '3. 填写参数或请求体',
        '4. 点击 "Execute" 发起请求',
        '',
        '## 认证说明',
        '所有接口都标了 @ApiBearerAuth，点击右上角 "Authorize" 按钮，',
        '填入任意字符串即可（本 Demo 不真正校验 token）。',
      ].join('\n'),
    )
    .setVersion('1.0.0')
    // 配置 Bearer Token 认证：
    // Swagger UI 右上角会出现 "Authorize" 按钮，填入 token 后所有接口
    // 自动在请求头带上 `Authorization: Bearer <token>`
    .addBearerAuth(
      {
        type: 'http',
        scheme: 'bearer',
        bearerFormat: 'JWT',
        description: '输入 JWT token（本 Demo 不校验，填任意字符串即可）',
      },
      'access-token', // 安全方案的 name，对应 @ApiBearerAuth('access-token')
    )
    .addTag('文章', '文章 CRUD 与发布接口')
    .addTag('用户', '用户注册与查询接口')
    .build();

  // 基于 AppModule 扫描所有装饰器元数据，生成 OpenAPI 文档对象
  const document = SwaggerModule.createDocument(app, config);

  // 把 Swagger UI 挂载到 /api-docs 路径
  // 第二个参数 document 是上一步生成的 OpenAPI 文档对象
  // 第三个参数是 UI 选项，可自定义路径与样式
  SwaggerModule.setup('api-docs', app, document, {
    swaggerOptions: {
      // 默认展开请求体示例
      docExpansion: 'none',
      // 显示请求耗时
      displayRequestDuration: true,
      // 持久化授权头（避免每次刷新都重新点 Authorize）
      persistAuthorization: true,
    },
    customSiteTitle: 'Day11 API 文档',
  });

  await app.listen(3000);

  logger.log('Day11 应用已启动：http://localhost:3000/api/v1');
  logger.log('Swagger UI：http://localhost:3000/api-docs');
  logger.log('OpenAPI JSON：http://localhost:3000/api-docs-json');
  logger.log('体验路径：');
  logger.log('  GET  /api/v1/articles               分页查询文章');
  logger.log('  POST /api/v1/articles               创建文章');
  logger.log('  GET  /api/v1/articles/1             获取文章详情');
  logger.log('  PATCH /api/v1/articles/1            更新文章');
  logger.log('  DELETE /api/v1/articles/1           删除文章');
  logger.log('  POST /api/v1/users                  创建用户（请求含密码，响应不含）');
}

bootstrap();
