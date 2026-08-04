import { Controller, Get, Inject, Injectable } from '@nestjs/common';
import {
  DATABASE_CONNECTION,
  DatabaseConnection,
} from './database-connection.provider';

/**
 * 异步 Provider 的消费者控制器。
 *
 * 容器在应用启动时已等待 useFactory 完成，
 * 因此这里直接同步注入即可拿到已就绪的连接对象。
 */
@Injectable()
@Controller()
export class AsyncProviderController {
  constructor(
    @Inject(DATABASE_CONNECTION) private readonly db: DatabaseConnection,
  ) {}

  @Get('async-db')
  check(): {
    host: string;
    port: number;
    connectedAt: number;
    ready: boolean;
    token: string;
  } {
    return {
      host: this.db.host,
      port: this.db.port,
      connectedAt: this.db.connectedAt,
      ready: true,
      token: DATABASE_CONNECTION.toString(),
    };
  }
}
