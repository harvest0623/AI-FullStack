/**
 * 统一响应封装
 *
 * 目标：让全项目所有接口返回结构一致，前端只需写一套解析逻辑。
 * 统一响应格式：{ code, message, data }
 *  - code: number，业务状态码。0 表示成功，非 0 表示业务错误。
 *  - message: string，人类可读的提示信息。
 *  - data: any，业务数据（对象 / 数组 / null）。
 */

/**
 * 成功响应
 * @param {import('express').Response} res - Express 响应对象
 * @param {*} data - 业务数据
 * @param {string} [message='操作成功'] - 提示信息
 * @param {number} [statusCode=200] - HTTP 状态码
 * @returns {import('express').Response}
 */
function success(res, data, message = '操作成功', statusCode = 200) {
  // 204 No Content 表示“成功但无内容返回”，HTTP 规范要求无 body
  if (statusCode === 204) {
    return res.status(204).end();
  }
  return res.status(statusCode).json({
    code: 0,
    message,
    data,
  });
}

/**
 * 错误响应
 * @param {import('express').Response} res - Express 响应对象
 * @param {string} [message='操作失败'] - 错误提示信息
 * @param {number} [statusCode=400] - HTTP 状态码
 * @param {number} [code=1] - 业务错误码（非 0 表示业务错误）
 * @returns {import('express').Response}
 */
function error(res, message = '操作失败', statusCode = 400, code = 1) {
  return res.status(statusCode).json({
    code,
    message,
    data: null,
  });
}

/**
 * 分页响应
 * 统一分页格式：
 * { code, message, data: { list, total, page, pageSize, totalPages } }
 *
 * @param {import('express').Response} res - Express 响应对象
 * @param {Object} payload - 分页数据
 * @param {Array} payload.list - 当前页数据
 * @param {number} payload.total - 符合条件的总记录数
 * @param {number} payload.page - 当前页码（从 1 开始）
 * @param {number} payload.pageSize - 每页条数
 * @param {string} [message='查询成功'] - 提示信息
 * @returns {import('express').Response}
 */
function paginate(res, { list, total, page, pageSize }, message = '查询成功') {
  return res.status(200).json({
    code: 0,
    message,
    data: {
      list,
      total,
      page,
      pageSize,
      // total 为 0 时 totalPages 至少为 1，避免前端出现“第 1 页 / 共 0 页”的尴尬
      totalPages: Math.max(1, Math.ceil(total / pageSize)),
    },
  });
}

module.exports = { success, error, paginate };
