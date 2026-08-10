import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { AppConfig, JwtConfig } from '../config/config.interface';

/**
 * Day12 Articles Service（演示 ConfigService 注入）
 *
 * 演示要点：
 *   1. 由于 ConfigModule 已 isGlobal，Service 直接注入 ConfigService 即可
 *   2. 嵌套配置用点号路径读取：get('app.port')、get('jwt.secret')
 *   3. 通过泛型 + 接口拿到强类型对象：get<AppConfig>('app')
 *   4. 第二个参数为默认值，配置缺失时回退
 *
 * 注意：
 *   - 这里只是演示配置读取，不涉及真正的文章 CRUD（Day10 已演示）
 *   - JWT 密钥读取为 Day14 鉴权铺垫
 */
@Injectable()
export class ArticlesService {
  private readonly logger = new Logger(ArticlesService.name);

  // 由于 ConfigModule 是全局的，构造函数注入即可，无需在 ArticlesModule 显式 import
  constructor(private readonly configService: ConfigService) {}

  /**
   * 返回一个包含当前应用基本信息的对象，用于演示读取应用配置
   */
  getAppInfo(): AppConfig {
    // 方式一：整块读取（推荐，类型推断最准确）
    const app = this.configService.get<AppConfig>('app');

    // 方式二：单字段读取，并指定类型 + 默认值
    const port = this.configService.get<number>('app.port', 3000);
    const env = this.configService.get<string>('app.env', 'development');

    this.logger.log(
      `读取应用配置 -> name=${app?.name}, env=${env}, port=${port}, prefix=${app?.prefix}`,
    );

    return (
      app ?? {
        name: 'nest-app',
        port,
        prefix: 'api/v1',
        env,
      }
    );
  }

  /**
   * 演示读取 JWT 配置（为 Day14 鉴权铺垫）
   *
   * 安全提示：
   *   - 真实业务中，JWT 密钥不应被返回到接口响应中
   *   - 这里仅做日志输出（且只输出长度，不输出明文）
   */
  getJwtInfo(): Pick<JwtConfig, 'expiresIn' | 'refreshExpiresIn'> & {
    secretLength: number;
  } {
    const secret = this.configService.get<string>('jwt.secret', '');
    const expiresIn = this.configService.get<string>('jwt.expiresIn', '1h');
    const refreshExpiresIn = this.configService.get<string>(
      'jwt.refreshExpiresIn',
      '7d',
    );

    this.logger.log(
      `读取 JWT 配置 -> secretLength=${secret.length}, expiresIn=${expiresIn}, refreshExpiresIn=${refreshExpiresIn}`,
    );

    return {
      secretLength: secret.length,
      expiresIn,
      refreshExpiresIn,
    };
  }

  /**
   * 演示读取数据库 URL（为 Day13 TypeORM 铺垫）
   */
  getDatabaseUrl(): string {
    return this.configService.get<string>('database.url', '');
  }
}
