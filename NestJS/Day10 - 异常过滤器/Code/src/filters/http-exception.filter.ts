import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpException,
  Logger,
} from '@nestjs/common';
import { Request, Response } from 'express';
import { ErrorResponseDto } from '../common/error-response.dto';

/**
 * HttpException 过滤器
 *
 * 只捕获 NestJS 内置的 HttpException 及其子类：
 *   BadRequestException / UnauthorizedException / NotFoundException /
 *   ForbiddenException / ConflictException / InternalServerErrorException /
 *   PayloadTooLargeException ...
 *
 * 职责：把 NestJS 默认的响应格式
 *   { statusCode, message, error }
 * 改写成统一格式
 *   { code, message, details, timestamp, path }
 *
 * 触发场景举例：
 *   - throw new NotFoundException('文章不存在')
 *   - ValidationPipe 校验失败抛出 BadRequestException
 *   - Guard 鉴权失败抛出 UnauthorizedException / ForbiddenException
 */
@Catch(HttpException)
export class HttpExceptionFilter implements ExceptionFilter {
  private readonly logger = new Logger(HttpExceptionFilter.name);

  catch(exception: HttpException, host: ArgumentsHost): void {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    const status = exception.getStatus();
    const exceptionResponse = exception.getResponse();

    // exceptionResponse 可能是：
    //   - string                       （throw new HttpException('msg', 400)）
    //   - { message: string | string[], error: string, statusCode: number }
    //                                 （内置子类异常的默认格式）
    //   - 自定义对象                    （throw new HttpException({...}, 400)）
    let message: string;
    let details: unknown;

    if (typeof exceptionResponse === 'string') {
      message = exceptionResponse;
    } else if (
      typeof exceptionResponse === 'object' &&
      exceptionResponse !== null
    ) {
      const resp = exceptionResponse as Record<string, unknown>;
      const rawMessage = resp['message'];
      // ValidationPipe 失败时 message 是 string[]，拼接成一行更易读
      message = Array.isArray(rawMessage)
        ? rawMessage.join('; ')
        : String(rawMessage ?? exception.message);
      // 内置异常的 error 字段（如 "Not Found"）放进 details
      if (resp['error']) {
        details = { error: resp['error'] };
      }
    } else {
      message = exception.message;
    }

    const body: ErrorResponseDto = {
      // 用 HTTP_<status> 作为 code，方便前端在没有业务码时兜底分支
      code: `HTTP_${status}`,
      message,
      details,
      timestamp: new Date().toISOString(),
      path: request.url,
    };

    // 4xx 用 warn 级别，避免污染 error 日志
    this.logger.warn(
      `${request.method} ${request.url} -> ${status} ${body.code}: ${message}`,
    );

    response.status(status).json(body);
  }
}
