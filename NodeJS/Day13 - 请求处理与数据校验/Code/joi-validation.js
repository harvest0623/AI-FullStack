/**
 * joi-validation.js
 * ----------------------------------------------------------------
 * 用 Joi 校验用户注册接口的入参，演示 schema 优先的校验方式。
 *
 * 重点演示：
 *   1. 定义 object / string / number / array / boolean / date schema
 *   2. required / optional / min / max / email / regex / valid 等规则
 *   3. stripUnknown 丢弃未知字段（防原型链污染）
 *   4. default 默认值、convert 自动类型转换
 *   5. abortEarly: false 一次性收集所有错误
 *   6. messages + 模板变量定制中文错误信息
 *   7. 包装为 Express 中间件，校验后用清洗值回写 req.body
 *
 * 运行：npm run joi   （node joi-validation.js）
 * 测试：见 server.js 注释中的 curl 命令
 * ----------------------------------------------------------------
 */

const express = require('express');
const Joi = require('joi');

const app = express();
app.use(express.json());

// ----------------------------------------------------------------
// 1. 定义注册接口的 schema
// ----------------------------------------------------------------
const registerSchema = Joi.object({
  // 用户名：3-20 位字母数字，必填
  username: Joi.string()
    .alphanum()
    .min(3)
    .max(20)
    .required()
    .messages({
      'string.alphanum': '用户名只能包含字母和数字',
      'string.min': '用户名至少 {#limit} 个字符',
      'string.max': '用户名最多 {#limit} 个字符',
      'string.empty': '用户名不能为空',
      'any.required': '缺少必填字段：用户名',
    }),

  // 邮箱：合法邮箱格式，必填
  email: Joi.string()
    .email({ tlds: { allow: false } })
    .required()
    .messages({
      'string.email': '邮箱格式不正确',
      'string.empty': '邮箱不能为空',
      'any.required': '缺少必填字段：邮箱',
    }),

  // 密码：8-32 位，必须同时包含字母和数字（正则断言）
  password: Joi.string()
    .pattern(/^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d!@#$%^&*]{8,32}$/)
    .required()
    .messages({
      'string.pattern.base': '密码 8-32 位，必须同时包含字母和数字',
      'string.empty': '密码不能为空',
      'any.required': '缺少必填字段：密码',
    }),

  // 年龄：18-100 的整数，可选
  age: Joi.number()
    .integer()
    .min(18)
    .max(100)
    .optional()
    .messages({
      'number.base': '年龄必须是数字',
      'number.integer': '年龄必须是整数',
      'number.min': '年龄不能小于 {#limit}',
      'number.max': '年龄不能大于 {#limit}',
    }),

  // 角色：枚举 user / vip，默认 user
  role: Joi.string()
    .valid('user', 'vip')
    .default('user')
    .messages({
      'any.only': '角色只能是 user 或 vip',
    }),

  // 标签：字符串数组，每个元素最多 20 字，最多 5 个
  tags: Joi.array()
    .items(Joi.string().max(20))
    .max(5)
    .optional()
    .messages({
      'array.max': '标签最多 {#limit} 个',
      'string.max': '单个标签最多 {#limit} 个字符',
    }),

  // 生日：日期，必须早于当前时间
  birthday: Joi.date()
    .less('now')
    .optional()
    .messages({
      'date.base': '生日必须是合法日期',
      'date.less': '生日必须早于今天',
    }),
})
  // 全局选项
  .options({
    stripUnknown: true, // 丢弃 schema 未声明的字段（防 __proto__ 注入与脏数据）
    abortEarly: false,  // 收集所有错误，而非遇首个即停
    convert: true,      // 自动类型转换（query 字符串 → 数字等）
  })
  .messages({
    'object.unknown': '存在未知字段：{#label}',
  });

// ----------------------------------------------------------------
// 2. 通用 Joi 校验中间件工厂
//    校验通过后用清洗值回写 req[source]，下游 controller 拿到的就是规范数据
// ----------------------------------------------------------------
function validate(schema, source = 'body') {
  return (req, res, next) => {
    const data = req[source];
    const { value, error } = schema.validate(data, { abortEarly: false, stripUnknown: true });

    if (error) {
      // 不在此处直接响应，而是把结构化错误抛给统一错误中间件
      return next({
        type: 'JOI_ERROR',
        error,
      });
    }

    // 用清洗后的值覆盖原值（已 trim / 已 cast / 已剥离未知字段）
    req[source] = value;
    next();
  };
}

// ----------------------------------------------------------------
// 3. 路由：用户注册
// ----------------------------------------------------------------
app.post(
  '/api/register',
  validate(registerSchema, 'body'),
  (req, res) => {
    // 此时 req.body 已经是经过 Joi 清洗的“干净数据”
    // controller 只需关心业务逻辑，无需再做格式校验
    const user = {
      ...req.body,
      id: Date.now(),
      createdAt: new Date().toISOString(),
    };

    res.json({
      success: true,
      data: user,
      message: '注册成功（演示用，未真实写库）',
    });
  }
);

// ----------------------------------------------------------------
// 4. 健康检查
// ----------------------------------------------------------------
app.get('/health', (req, res) => res.json({ success: true, message: 'joi-validation 服务运行中' }));

// ----------------------------------------------------------------
// 5. 启动服务（单独运行本文件时）
// ----------------------------------------------------------------
if (require.main === module) {
  const PORT = 3001;
  app.listen(PORT, () => {
    console.log(`[joi-validation] 服务已启动：http://localhost:${PORT}`);
    console.log('  POST /api/register  用户注册（Joi 校验）');
    console.log('  GET  /health        健康检查');
    console.log('\n示例 curl：');
    console.log('  curl -X POST http://localhost:3001/api/register \\');
    console.log('    -H "Content-Type: application/json" \\');
    console.log('    -d \'{"username":"alice","email":"a@b.com","password":"abc12345","age":20}\'');
  });
}

// 导出供 server.js 组合使用
module.exports = { app, registerSchema, validate };
