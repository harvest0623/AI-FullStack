import 'reflect-metadata';
import { NestFactory } from '@nestjs/core';
import { ConfigService } from '@nestjs/config';
import { Logger } from '@nestjs/common';
import { AppModule } from './app.module';

/**
 * Day12 启动入口
 *
 * 演示要点：
 *   1. 所有配置由 ConfigModule.forRoot() 在启动期加载并校验
 *   2. main.ts 通过 app.get(ConfigService) 拿到端口与前缀，不再硬编码 3000
 *   3. 端口、前缀都来自环境变量，生产/开发可不同
 *
 * 启动流程：
 *   AppModule 构造 -> ConfigModule 加载 .env + Joi 校验 -> 注册命名空间配置
 *   -> NestFactory.create -> app.listen(配置中的端口)
 *
 * 启动命令示例：
 *   npm run start:dev                                  # 默认 development
 *   NODE_ENV=production npm run start:prod             # 生产配置
 */
async function bootstrap() {
  const logger = new Logger('Bootstrap');
  const app = await NestFactory.create(AppModule);

  // 从 ConfigService 读取应用配置（不再硬编码）
  const configService = app.get(ConfigService);
  const port = configService.get<number>('app.port', 3000);
  const prefix = configService.get<string>('app.prefix', 'api/v1');
  const env = configService.get<string>('app.env', 'development');

  app.setGlobalPrefix(prefix);

  await app.listen(port);
  logger.log(`Day12 配置管理 Demo 已启动`);
  logger.log(`  环境:    ${env}`);
  logger.log(`  地址:    http://localhost:${port}/${prefix}`);
  logger.log(`  日志级别: ${configService.get<string>('log.level', 'log')}`);
  logger.log(`  数据库:  ${configService.get<string>('database.host')}:${configService.get<string>('database.port')}`);
}

bootstrap();
