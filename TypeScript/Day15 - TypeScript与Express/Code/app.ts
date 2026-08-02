import express, { type Express, type RequestHandler } from 'express';
// 注意：types/express.d.ts 通过 declare module 自动生效，无需显式 import
// （.d.ts 是纯类型声明文件，import 它会在运行时报 MODULE_NOT_FOUND）

import { logger } from './middlewares/logger';
import { errorHandler } from './middlewares/error-handler';
import articlesRouter from './routes/articles';
import { sendError, sendSuccess } from './utils/response';

const app: Express = express();

// ====================== 基础中间件 ======================
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(logger);

// ====================== 健康检查 ======================
app.get('/health', (_req, res) => {
  sendSuccess(res, { status: 'ok', uptime: process.uptime() }, '健康检查');
});

// ====================== 业务路由 ======================
app.use('/api/articles', articlesRouter);

// ====================== 404 兜底 ======================
// 必须在所有业务路由之后注册
const notFoundHandler: RequestHandler = (req, res) => {
  sendError(
    res,
    404,
    `路由不存在: ${req.method} ${req.originalUrl}`,
    'NOT_FOUND',
    undefined,
    req.requestId,
  );
};
app.use(notFoundHandler);

// ====================== 全局错误处理 ======================
// 必须放在所有路由 / 中间件之后，且参数为 4 个 (err, req, res, next)
app.use(errorHandler);

export default app;
