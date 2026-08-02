import { Router } from 'express';
import type { Request, Response } from 'express';
import { asyncHandler } from '../middlewares/async-handler';
import { auth } from '../middlewares/auth';
import { articleService } from '../services/article-service';
import { sendSuccess } from '../utils/response';
import {
  ValidationError,
  type ArticleListQuery,
  type CreateArticleDTO,
  type UpdateArticleDTO,
} from '../types';

const router = Router();

/**
 * 文章路由
 * --------------------------------------------------------
 * 通过 Request<TParams, TResBody, TReqBody, TReqQuery> 四个泛型参数
 * 精确约束每个路由的入参形态，让 req.params / req.body / req.query 全部类型安全。
 *
 * 路由参数（如 :id）始终是 string 类型，需要在处理函数内显式转换并校验。
 */

// GET /api/articles?page=1&pageSize=10&keyword=ts
router.get(
  '/',
  asyncHandler(
    async (
      req: Request<Record<string, never>, unknown, unknown, ArticleListQuery>,
      res: Response,
    ) => {
      const result = await articleService.list(req.query);
      sendSuccess(res, result, '文章列表', req.requestId);
    },
  ),
);

// GET /api/articles/:id
router.get(
  '/:id',
  asyncHandler(async (req: Request<{ id: string }>, res: Response) => {
    const id = Number(req.params.id);
    if (Number.isNaN(id)) {
      throw new ValidationError('id 必须是数字', { id: req.params.id });
    }
    const article = await articleService.getById(id);
    sendSuccess(res, article, '文章详情', req.requestId);
  }),
);

// POST /api/articles  （需要鉴权）
router.post(
  '/',
  auth,
  asyncHandler(
    async (req: Request<Record<string, never>, unknown, CreateArticleDTO>, res: Response) => {
      // auth 中间件已确保 req.user 存在，此处类型层再次断言
      if (!req.user) throw new ValidationError('用户信息缺失');
      const article = await articleService.create(req.body, req.user.id);
      sendSuccess(res, article, '创建成功', req.requestId);
    },
  ),
);

// PUT /api/articles/:id  （需要鉴权）
router.put(
  '/:id',
  auth,
  asyncHandler(
    async (req: Request<{ id: string }, unknown, UpdateArticleDTO>, res: Response) => {
      const id = Number(req.params.id);
      if (Number.isNaN(id)) {
        throw new ValidationError('id 必须是数字', { id: req.params.id });
      }
      const article = await articleService.update(id, req.body);
      sendSuccess(res, article, '更新成功', req.requestId);
    },
  ),
);

// DELETE /api/articles/:id  （需要鉴权）
router.delete(
  '/:id',
  auth,
  asyncHandler(async (req: Request<{ id: string }>, res: Response) => {
    const id = Number(req.params.id);
    if (Number.isNaN(id)) {
      throw new ValidationError('id 必须是数字', { id: req.params.id });
    }
    await articleService.remove(id);
    sendSuccess(res, null, '删除成功', req.requestId);
  }),
);

export default router;
