import { Injectable, LoggerService as NestLoggerService, Scope } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as winston from 'winston';
import DailyRotateFile from 'winston-daily-rotate-file';
import * as path from 'path';

/**
 * 自定义 Logger 服务
 *
 * 本类演示三件事：
 *   1. 实现 NestJS 的 LoggerService 接口（log/error/warn/debug/verbose）
 *   2. 内部用 winston 作为日志后端，支持按日期切割文件、JSON 格式输出
 *   3. 通过 context 字段标识来源模块，便于排查
 *
 * 使用方式：
 *   - 全局：在 main.ts 中 app.useLogger(app.get(MyLoggerService))
 *   - 局部：构造函数 new MyLoggerService(MyService.name)
 *   - 注入：在模块 providers 里 { provide: 'Logger', useClass: MyLoggerService }
 *
 * 为什么选 winston？
 *   - 内置 Logger 只能输出到控制台
 *   - winston 支持 transports（多目的地：console + file + http）
 *   - 配合 winston-daily-rotate-file 自动按日切割、保留 N 天
 *   - JSON 格式输出，方便 ELK / Loki / CloudWatch 采集
 *
 * 注意：本类使用 Scope.DEFAULT（单例），避免每个注入点都创建新的 winston 实例。
 * context 通过构造函数参数传入，作为字段附加到每条日志上。
 */
@Injectable({ scope: Scope.DEFAULT })
export class MyLoggerService implements NestLoggerService {
  private readonly winston: winston.Logger;
  private context: string;
  private readonly level: string;

  constructor(context?: string, config?: ConfigService) {
    // 允许构造时指定 context；若未指定则用类名
    this.context = context || 'Application';

    // 兼容被 NestJS 容器实例化（无参）与手动 new（带 config）两种情况
    const envLevel = process.env.LOG_LEVEL || 'debug';
    const logDir = process.env.LOG_DIR || './logs';
    this.level = (config?.get<string>('LOG_LEVEL') || envLevel).toLowerCase();

    // 确保日志目录存在（在 winston transports 内会自动创建，这里只是兜底）
    const absLogDir = path.resolve(process.cwd(), logDir);

    // 自定义 JSON 格式：附加上下文、时间戳、进程信息
    const jsonFormat = winston.format.combine(
      winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss.SSS' }),
      winston.format.errors({ stack: true }),
      winston.format.json(),
    );

    // 控制台彩色格式（开发环境友好）
    const consoleFormat = winston.format.combine(
      winston.format.colorize({ all: true }),
      winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
      winston.format.printf(({ timestamp, level, message, context, ...meta }) => {
        const ctx = context || 'App';
        const metaStr = Object.keys(meta).length ? ` ${JSON.stringify(meta)}` : '';
        return `${timestamp} [${level}] [${ctx}] ${message}${metaStr}`;
      }),
    );

    this.winston = winston.createLogger({
      level: this.level,
      defaultMeta: {
        service: 'nest-day15',
        pid: process.pid,
      },
      transports: [
        // 1) 控制台：开发环境用彩色
        new winston.transports.Console({
          format: consoleFormat,
        }),

        // 2) 按日切割的 all 日志文件
        new DailyRotateFile({
          dirname: absLogDir,
          filename: 'app-%DATE%.log',
          datePattern: 'YYYY-MM-DD',
          maxSize: '20m',
          maxFiles: '14d',
          format: jsonFormat,
        }),

        // 3) 按日切割的 error 日志文件（仅 level=error 及以上）
        new DailyRotateFile({
          dirname: absLogDir,
          filename: 'error-%DATE%.log',
          datePattern: 'YYYY-MM-DD',
          maxSize: '20m',
          maxFiles: '30d',
          level: 'error',
          format: jsonFormat,
        }),
      ],
    });
  }

  /**
   * 设置/覆盖 context（NestJS 内置 Logger 提供，便于全局单例复用）
   */
  setContext(context: string) {
    this.context = context;
  }

  /**
   * 自定义 context 版本（每次输出可附带临时 context）
   * 例如：logger.log('msg', 'TempCtx')
   */
  log(message: any, context?: string): void {
    this.winston.info(this.stringify(message), {
      context: context || this.context,
    });
  }

  error(message: any, trace?: string, context?: string): void {
    this.winston.error(this.stringify(message), {
      context: context || this.context,
      trace: trace,
    });
  }

  warn(message: any, context?: string): void {
    this.winston.warn(this.stringify(message), {
      context: context || this.context,
    });
  }

  debug(message: any, context?: string): void {
    this.winston.debug(this.stringify(message), {
      context: context || this.context,
    });
  }

  verbose(message: any, context?: string): void {
    this.winston.verbose(this.stringify(message), {
      context: context || this.context,
    });
  }

  /**
   * 把对象/数组转换为字符串，避免 winston 把 Error 序列化丢失 stack
   */
  private stringify(value: any): string {
    if (typeof value === 'string') return value;
    if (value instanceof Error) return `${value.message}\n${value.stack || ''}`;
    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
  }
}
