import { Controller, Get } from '@nestjs/common';
import { ArticlesService } from './articles.service';

/**
 * Day12 Articles Controller
 *
 * 仅暴露一个调试接口，用来验证配置链路是否打通：
 *   GET /api/v1/articles/config-demo
 *
 * 真实业务接口（CRUD）请参考 Day02 / Day10 的实现，这里不重复。
 */
@Controller('articles')
export class ArticlesController {
  constructor(private readonly articlesService: ArticlesService) {}

  /**
   * 演示接口：返回当前应用配置快照（已脱敏）
   *
   * 响应示例：
   *   {
   *     "app": { "name": "nest-day12-config-demo", "port": 3000, ... },
   *     "jwt": { "expiresIn": "1h", "secretLength": 41 },
   *     "databaseUrl": "postgresql://..."
   *   }
   */
  @Get('config-demo')
  getConfigDemo() {
    return {
      app: this.articlesService.getAppInfo(),
      jwt: this.articlesService.getJwtInfo(),
      databaseUrl: this.articlesService.getDatabaseUrl(),
    };
  }
}
