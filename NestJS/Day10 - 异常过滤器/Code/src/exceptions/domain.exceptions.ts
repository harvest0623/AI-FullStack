import { BusinessException } from './business.exception';
import { ExceptionCode } from './exception-code.constants';

/**
 * 领域异常集合
 *
 * 每个领域异常封装一个常见的业务错误场景：
 *   - 自动填充合适的 errorCode / httpStatus / message
 *   - 调用方只需 throw new XxxException(id)，无需重复传业务码
 *
 * 这种"领域异常"模式的优点：
 *   1. 业务码集中管理，避免散落在各处硬编码
 *   2. Service 层代码更可读：throw new ArticleNotFoundException(id)
 *      比 throw new BusinessException('ARTICLE_NOT_FOUND', '文章不存在: ' + id) 清晰
 *   3. 异常名本身即文档，IDE 自动补全可看到所有可能抛出的异常
 */

/**
 * 用户域异常：找不到指定用户
 *
 * 示例：
 *   throw new UserNotFoundException('user-123');
 *   throw new UserNotFoundException(100);
 */
export class UserNotFoundException extends BusinessException {
  constructor(identifier: string | number, options?: { cause?: unknown }) {
    super(ExceptionCode.USER_NOT_FOUND, `用户不存在: ${identifier}`, {
      details: { identifier },
      cause: options?.cause,
    });
  }
}

/**
 * 文章域异常：找不到指定文章
 */
export class ArticleNotFoundException extends BusinessException {
  constructor(articleId: string | number, options?: { cause?: unknown }) {
    super(ExceptionCode.ARTICLE_NOT_FOUND, `文章不存在: ${articleId}`, {
      details: { articleId },
      cause: options?.cause,
    });
  }
}

/**
 * 文章域异常：文章被锁定，无法修改
 * 映射到 HTTP 423 Locked
 */
export class ArticleLockedException extends BusinessException {
  constructor(articleId: string | number, options?: { cause?: unknown }) {
    super(ExceptionCode.ARTICLE_LOCKED, `文章已被锁定，无法修改: ${articleId}`, {
      details: { articleId },
      cause: options?.cause,
    });
  }
}

/**
 * 校验异常：手动校验失败时抛出
 *
 * 与 class-validator + ValidationPipe 自动校验互补：
 *   - DTO 自动校验：处理请求体格式错误（字段类型、长度等）
 *   - 手动 ValidationException：处理跨字段、依赖数据库的校验
 *     例如"邮箱已存在"、"余额不足"等
 */
export class ValidationException extends BusinessException {
  constructor(message: string, details?: unknown) {
    super(ExceptionCode.VALIDATION_FAILED, message, { details });
  }
}
