/**
 * 文章资源 CRUD 路由（express.Router）
 *
 * 资源：/api/v1/articles
 * 存储：内存数组（模拟数据库，重启即重置）
 *
 * 路由映射：
 *   GET    /            列表（支持分页、过滤、排序）   200
 *   GET    /:id         详情                          200 / 404
 *   POST   /            创建                          201 / 422
 *   PUT    /:id         全量更新                      200 / 404 / 422
 *   PATCH  /:id         部分更新                      200 / 404 / 422
 *   DELETE /:id         删除                          204 / 404
 */

const express = require('express');
const { success, error, paginate } = require('./response-helper');
const { asyncHandler } = require('./async-handler');

const router = express.Router();

// ---------------------------------------------------------------------------
// 内存数据存储（模拟数据库）
// ---------------------------------------------------------------------------
let articles = [
  {
    id: 1,
    title: 'Express 入门指南',
    content: 'Express 是 Node.js 最流行的 Web 框架，核心是路由与中间件。',
    author: 'Alice',
    tags: ['node', 'express'],
    createdAt: '2026-01-01T00:00:00.000Z',
    updatedAt: '2026-01-01T00:00:00.000Z',
  },
  {
    id: 2,
    title: 'RESTful API 设计',
    content: 'REST 是一种架构风格，强调资源、统一接口与无状态。',
    author: 'Bob',
    tags: ['rest', 'api'],
    createdAt: '2026-01-02T00:00:00.000Z',
    updatedAt: '2026-01-02T00:00:00.000Z',
  },
  {
    id: 3,
    title: 'AI 全栈开发实战',
    content: '从大模型调用到工程化落地的完整路径。',
    author: 'Carol',
    tags: ['ai', 'node'],
    createdAt: '2026-01-03T00:00:00.000Z',
    updatedAt: '2026-01-03T00:00:00.000Z',
  },
];
// 下一个自增 id
let nextId = 4;

// ---------------------------------------------------------------------------
// 工具函数
// ---------------------------------------------------------------------------

/**
 * 解析分页查询参数，做边界处理
 * - page 最小为 1，非法值回退到 1
 * - pageSize 默认 10，上限 100，防止超大分页拖垮服务
 * @param {Object} query - req.query
 * @returns {{ page: number, pageSize: number }}
 */
function parsePagination(query) {
  const page = Math.max(1, parseInt(query.page, 10) || 1);
  const pageSize = Math.max(1, Math.min(100, parseInt(query.pageSize, 10) || 10));
  return { page, pageSize };
}

// 业务错误码约定（四位数字，便于前端区分）
const BIZ_CODE = {
  NOT_FOUND: 4040,   // 资源不存在
  VALIDATION: 4220,  // 参数校验失败
};

// ---------------------------------------------------------------------------
// 路由定义
// ---------------------------------------------------------------------------

/**
 * GET /api/v1/articles
 * 列表查询，支持分页、过滤、排序
 *
 * Query 参数：
 *   page      - 页码（默认 1）
 *   pageSize  - 每页条数（默认 10，上限 100）
 *   author    - 按作者精确过滤（忽略大小写）
 *   keyword   - 标题/内容模糊搜索
 *   sort      - 排序，格式 field:asc 或 field:desc
 */
router.get(
  '/',
  asyncHandler(async (req, res) => {
    const { page, pageSize } = parsePagination(req.query);

    // 先复制一份，避免修改原数组
    let result = [...articles];

    // 过滤：按作者
    if (req.query.author) {
      const author = req.query.author.toLowerCase();
      result = result.filter((a) => a.author.toLowerCase() === author);
    }

    // 过滤：关键词搜索（标题或内容包含）
    if (req.query.keyword) {
      const kw = req.query.keyword.toLowerCase();
      result = result.filter(
        (a) =>
          a.title.toLowerCase().includes(kw) ||
          a.content.toLowerCase().includes(kw)
      );
    }

    // 排序：格式 sort=field:desc，默认升序
    if (req.query.sort) {
      const [field, order = 'asc'] = req.query.sort.split(':');
      const dir = order === 'desc' ? -1 : 1;
      result.sort((a, b) => {
        if (a[field] < b[field]) return -1 * dir;
        if (a[field] > b[field]) return 1 * dir;
        return 0;
      });
    }

    // 分页切片
    const total = result.length;
    const start = (page - 1) * pageSize;
    const list = result.slice(start, start + pageSize);

    return paginate(res, { list, total, page, pageSize });
  })
);

/**
 * GET /api/v1/articles/:id
 * 获取单篇文章详情
 */
router.get(
  '/:id',
  asyncHandler(async (req, res) => {
    const id = parseInt(req.params.id, 10);
    const article = articles.find((a) => a.id === id);

    if (!article) {
      return error(res, `文章 id=${id} 不存在`, 404, BIZ_CODE.NOT_FOUND);
    }

    return success(res, article, '查询成功');
  })
);

/**
 * POST /api/v1/articles
 * 创建文章，返回 201 + 新资源
 *
 * Body：
 *   title*   - 标题（必填）
 *   content* - 内容（必填）
 *   author   - 作者（默认“匿名”）
 *   tags     - 标签数组
 */
router.post(
  '/',
  asyncHandler(async (req, res) => {
    const { title, content, author, tags } = req.body || {};

    // 校验必填字段
    if (!title || !content) {
      return error(res, 'title 和 content 为必填项', 422, BIZ_CODE.VALIDATION);
    }

    const now = new Date().toISOString();
    const article = {
      id: nextId++,
      title,
      content,
      author: author || '匿名',
      tags: Array.isArray(tags) ? tags : [],
      createdAt: now,
      updatedAt: now,
    };

    articles.push(article);
    return success(res, article, '创建成功', 201);
  })
);

/**
 * PUT /api/v1/articles/:id
 * 全量更新——客户端必须提供全部字段，未提供的会被覆盖
 *
 * 幂等性：用同一份 body 重复 PUT，结果不变
 */
router.put(
  '/:id',
  asyncHandler(async (req, res) => {
    const id = parseInt(req.params.id, 10);
    const index = articles.findIndex((a) => a.id === id);

    if (index === -1) {
      return error(res, `文章 id=${id} 不存在`, 404, BIZ_CODE.NOT_FOUND);
    }

    const { title, content, author, tags } = req.body || {};

    // PUT 要求全量，必填字段必须提供
    if (!title || !content) {
      return error(
        res,
        'PUT 全量更新需提供 title 和 content',
        422,
        BIZ_CODE.VALIDATION
      );
    }

    const now = new Date().toISOString();
    articles[index] = {
      ...articles[index],
      title,
      content,
      author: author || articles[index].author,
      tags: Array.isArray(tags) ? tags : articles[index].tags,
      updatedAt: now,
    };

    return success(res, articles[index], '更新成功');
  })
);

/**
 * PATCH /api/v1/articles/:id
 * 部分更新——只传要改的字段，未传字段保持不变
 *
 * 使用白名单机制，只允许更新 title/content/author/tags，
 * 防止客户端篡改 id、createdAt 等不可变字段
 */
router.patch(
  '/:id',
  asyncHandler(async (req, res) => {
    const id = parseInt(req.params.id, 10);
    const index = articles.findIndex((a) => a.id === id);

    if (index === -1) {
      return error(res, `文章 id=${id} 不存在`, 404, BIZ_CODE.NOT_FOUND);
    }

    // 白名单字段
    const allowedFields = ['title', 'content', 'author', 'tags'];
    const updates = {};
    let hasUpdate = false;

    for (const field of allowedFields) {
      if (req.body && Object.prototype.hasOwnProperty.call(req.body, field)) {
        updates[field] = req.body[field];
        hasUpdate = true;
      }
    }

    if (!hasUpdate) {
      return error(
        res,
        '未提供任何可更新字段（title/content/author/tags）',
        422,
        BIZ_CODE.VALIDATION
      );
    }

    articles[index] = {
      ...articles[index],
      ...updates,
      updatedAt: new Date().toISOString(),
    };

    return success(res, articles[index], '部分更新成功');
  })
);

/**
 * DELETE /api/v1/articles/:id
 * 删除文章，返回 204 No Content
 *
 * 幂等性：重复删除最终资源都是“不存在”
 */
router.delete(
  '/:id',
  asyncHandler(async (req, res) => {
    const id = parseInt(req.params.id, 10);
    const index = articles.findIndex((a) => a.id === id);

    if (index === -1) {
      return error(res, `文章 id=${id} 不存在`, 404, BIZ_CODE.NOT_FOUND);
    }

    articles.splice(index, 1);
    // 204 无内容返回
    return success(res, null, '删除成功', 204);
  })
);

module.exports = router;
