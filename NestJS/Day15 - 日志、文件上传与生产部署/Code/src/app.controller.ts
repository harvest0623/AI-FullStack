import { Controller, Get } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { MyLoggerService } from './logger/my-logger.service';

/**
 * 根路由控制器
 * 用于演示：
 *   - 配置读取
 *   - 自定义 Logger 注入与按 context 输出
 */
@Controller()
export class AppController {
  private readonly logger = new MyLoggerService(AppController.name);

  constructor(private readonly config: ConfigService) {}

  @Get()
  root() {
    this.logger.log('访问根路由');
    return {
      name: 'NestJS Day15',
      version: '1.0.0',
      env: this.config.get<string>('NODE_ENV', 'development'),
      timestamp: new Date().toISOString(),
      docs: [
        'GET  /api/v1/health',
        'POST /api/v1/upload/single  (form-data: file)',
        'POST /api/v1/upload/multiple (form-data: files)',
        'POST /api/v1/upload/avatar   (form-data: file, only jpg/png <2MB)',
      ],
    };
  }
}
