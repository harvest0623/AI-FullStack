import type { RequestHandler } from 'express';
import { UnauthorizedError, ForbiddenError, type RequestUser } from '../types';

/**
 * 鉴权中间件
 * --------------------------------------------------------
 * 通过 Authorization: Bearer <token> 解析当前用户，挂载到 req.user
 * 真实场景应配合 JWT / Session / OAuth，这里用 fake token 演示
 */

// 假装的 token -> 用户映射，生产环境请用 JWT 解码或 Redis 查询
const FAKE_USER_MAP: Record<string, RequestUser> = {
  'admin-token': { id: '1', name: '管理员', role: 'admin' },
  'user-token': { id: '2', name: '普通用户', role: 'user' },
};

export const auth: RequestHandler = (req, _res, next) => {
  const header = req.headers.authorization;
  if (!header || !header.startsWith('Bearer ')) {
    return next(new UnauthorizedError('缺少 Authorization 头或格式错误'));
  }

  const token = header.slice(7);
  const user = FAKE_USER_MAP[token];
  if (!user) {
    return next(new UnauthorizedError('无效的 token'));
  }

  // 类型安全：req.user 由 express.d.ts 扩展声明
  req.user = user;
  next();
};

/**
 * 角色守卫工厂
 * --------------------------------------------------------
 * 返回一个新的 RequestHandler，用于校验 req.user.role 是否满足要求
 * 这是 NestJS Guard 的最小内核 —— 工厂 + 元数据 + 反射
 */
export const requireRole = (role: RequestUser['role']): RequestHandler => {
  return (req, _res, next) => {
    if (!req.user) {
      return next(new UnauthorizedError('未登录'));
    }
    if (req.user.role !== role) {
      return next(new ForbiddenError(`需要 ${role} 角色才能访问`));
    }
    next();
  };
};
