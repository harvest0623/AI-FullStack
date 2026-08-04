import { Injectable } from '@nestjs/common';

/**
 * LoggerService
 *
 * 一个最简的日志服务，被 @Global 的 CommonModule 通过 exports 暴露。
 * 因此 ArticlesService、UsersService 都可以直接注入它，无需在各自模块再 import CommonModule。
 */
@Injectable()
export class LoggerService {
  log(message: string) {
    // eslint-disable-next-line no-console
    console.log(`[LOG] ${new Date().toISOString()} - ${message}`);
  }

  warn(message: string) {
    // eslint-disable-next-line no-console
    console.warn(`[WARN] ${new Date().toISOString()} - ${message}`);
  }

  error(message: string) {
    // eslint-disable-next-line no-console
    console.error(`[ERROR] ${new Date().toISOString()} - ${message}`);
  }
}
