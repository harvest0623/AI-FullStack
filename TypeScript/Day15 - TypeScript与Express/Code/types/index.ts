/**
 * Day15 - 自定义类型与错误体系
 * --------------------------------------------------------
 * 该文件是整个应用的"类型契约中心"：
 * - 领域模型：描述数据库实体形态
 * - DTO：描述接口入参 / 出参形态，隔离内部模型与对外契约
 * - 服务接口：约束服务层实现，便于未来切换 / 替换 / 在 NestJS 中作为 Provider
 * - 自定义 Error：让错误处理中间件能按类型分支，输出合适的状态码
 */

// ====================== 领域模型 ======================
export interface Article {
  id: number;
  title: string;
  content: string;
  authorId: string;
  createdAt: string;
  updatedAt: string;
}

// ====================== DTO（Data Transfer Object）======================
/** 创建文章请求体 */
export interface CreateArticleDTO {
  title: string;
  content: string;
}

/** 更新文章请求体（所有字段可选，对应 HTTP PUT/PATCH 语义） */
export type UpdateArticleDTO = Partial<Pick<Article, 'title' | 'content'>>;

/** 文章列表查询参数（来自 query string，原始值均为 string） */
export interface ArticleListQuery {
  page?: string;
  pageSize?: string;
  keyword?: string;
}

/** 文章对外响应体（剥离 authorId 等内部字段） */
export type ArticleDTO = Omit<Article, 'authorId'>;

/** 通用分页响应 */
export interface PaginatedDTO<T> {
  list: T[];
  total: number;
  page: number;
  pageSize: number;
}

// ====================== 服务层接口 ======================
/**
 * 服务层契约：所有方法返回 Promise，便于未来切换为异步存储
 * 在 NestJS 中，此类会被标注 @Injectable()，并由 Controller 通过构造函数注入
 */
export interface IArticleService {
  list(query: ArticleListQuery): Promise<PaginatedDTO<ArticleDTO>>;
  getById(id: number): Promise<ArticleDTO>;
  create(input: CreateArticleDTO, authorId: string): Promise<ArticleDTO>;
  update(id: number, input: UpdateArticleDTO): Promise<ArticleDTO>;
  remove(id: number): Promise<void>;
}

// ====================== 上下文用户 ======================
/** 鉴权后挂载到 req.user 上的用户信息 */
export interface RequestUser {
  id: string;
  name: string;
  role: 'admin' | 'user';
}

// ====================== 统一响应体 ======================
/**
 * 统一响应封装
 * - 成功：code = 0，data 必填
 * - 失败：code = HTTP 状态码，errorType 标识错误类型，data 可选（错误详情）
 */
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data?: T;
  errorType?: string;
  requestId?: string;
  timestamp: string;
}

// ====================== 自定义错误体系 ======================
/**
 * 业务错误基类
 * 关键点：
 * 1. 继承 Error，保留 stack 与 instanceof 行为
 * 2. 通过 Object.setPrototypeOf 修复原型链（TS 编译到 ES5 后 instanceof 会失效）
 * 3. 携带 statusCode / code / details，让错误处理中间件能直接读取
 */
export class AppError extends Error {
  public readonly statusCode: number;
  public readonly code: string;
  public readonly details?: unknown;

  constructor(
    message: string,
    statusCode = 500,
    code = 'INTERNAL_ERROR',
    details?: unknown,
  ) {
    super(message);
    this.name = this.constructor.name;
    this.statusCode = statusCode;
    this.code = code;
    this.details = details;
    // 修复 ES5 target 下子类 instanceof 失效问题
    Object.setPrototypeOf(this, new.target.prototype);
    Error.captureStackTrace?.(this, this.constructor);
  }
}

/** 资源不存在（404） */
export class NotFoundError extends AppError {
  constructor(resource: string, id: string | number) {
    super(`${resource} ${id} 不存在`, 404, 'NOT_FOUND');
  }
}

/** 参数校验失败（400） */
export class ValidationError extends AppError {
  constructor(message: string, details?: unknown) {
    super(message, 400, 'VALIDATION_ERROR', details);
  }
}

/** 未授权（401） */
export class UnauthorizedError extends AppError {
  constructor(message = '未授权访问') {
    super(message, 401, 'UNAUTHORIZED');
  }
}

/** 禁止访问（403） */
export class ForbiddenError extends AppError {
  constructor(message = '禁止访问') {
    super(message, 403, 'FORBIDDEN');
  }
}
