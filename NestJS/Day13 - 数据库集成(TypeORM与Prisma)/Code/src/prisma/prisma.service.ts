import { Injectable, OnModuleInit, OnModuleDestroy, Logger } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';

/**
 * PrismaService
 *
 * 继承 PrismaClient，让所有 prisma.article / prisma.user 等代理直接可用。
 * 通过 OnModuleInit / OnModuleDestroy 钩子管理连接生命周期：
 *   - onModuleInit：模块初始化时 $connect()
 *   - onModuleDestroy：应用关闭时 $disconnect()
 *
 * 在 NestJS 里它是一个 @Injectable 单例，由 PrismaModule 统一提供。
 */
@Injectable()
export class PrismaService
  extends PrismaClient
  implements OnModuleInit, OnModuleDestroy
{
  private readonly logger = new Logger(PrismaService.name);

  async onModuleInit(): Promise<void> {
    await this.$connect();
    this.logger.log('Prisma 已连接数据库');
  }

  async onModuleDestroy(): Promise<void> {
    await this.$disconnect();
    this.logger.log('Prisma 已断开连接');
  }
}
