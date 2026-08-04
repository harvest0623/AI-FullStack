import 'reflect-metadata';
import { NestFactory } from '@nestjs/core';
import { Logger } from '@nestjs/common';
import { AppModule } from './app.module';

async function bootstrap() {
  const logger = new Logger('Bootstrap');
  const app = await NestFactory.create(AppModule);

  // 启动后让 MiniIoc 容器自检一次，演示自定义 IoC 容器的运行效果
  const { runMiniIocDemo } = await import('./mini-ioc/mini-container');
  await runMiniIocDemo();

  await app.listen(3000);
  logger.log('Day05 依赖注入深入 Demo 已启动：http://localhost:3000');
  logger.log('可用路由：');
  logger.log('  GET  /scope              对比 DEFAULT / REQUEST / TRANSIENT 三种作用域实例');
  logger.log('  GET  /token              对比类 / 字符串 / Symbol 三种 Token 注入');
  logger.log('  GET  /circular           演示 forwardRef 解决循环依赖');
  logger.log('  GET  /async-db           演示 useFactory 异步初始化数据库连接');
}

bootstrap();
