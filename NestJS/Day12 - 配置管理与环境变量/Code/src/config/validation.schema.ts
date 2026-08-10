import * as Joi from 'joi';

/**
 * 环境变量校验 Schema
 *
 * 用途：
 *   在 ConfigModule.forRoot({ validationSchema }) 中传入，
 *   启动时校验 process.env 中的字段是否符合预期。
 *
 * fail fast 原则：
 *   - 缺失必填项 -> 启动直接报错，避免运行时才发现配置缺失
 *   - 类型不匹配 -> 端口不是数字、URL 不符合格式等都立即拒绝
 *   - 非法值     -> 例如 NODE_ENV 只允许 development/production/test
 *
 * 设计要点：
 *   1. 必填字段用 .required()，可选字段用 .default()
 *   2. 数字用 Joi.number()，避免端口被当成字符串
 *   3. 枚举用 .valid()，限制取值范围
 *   4. 字符串最小长度可限制密钥强度（如 JWT_SECRET 至少 16 字符）
 */
export const validationSchema = Joi.object({
  // ===== 应用层 =====
  NODE_ENV: Joi.string()
    .valid('development', 'production', 'test')
    .default('development'),
  APP_NAME: Joi.string().default('nest-app'),
  APP_PORT: Joi.number().port().default(3000),
  APP_PREFIX: Joi.string().default('api/v1'),

  // ===== 数据库 =====
  DATABASE_HOST: Joi.string().default('localhost'),
  DATABASE_PORT: Joi.number().port().default(5432),
  DATABASE_USERNAME: Joi.string().default('postgres'),
  DATABASE_PASSWORD: Joi.string().allow('').default(''),
  DATABASE_NAME: Joi.string().default('nest_app'),
  // 生产环境通常要求 URL 格式为 postgresql://...
  DATABASE_URL: Joi.string()
    .optional()
    .pattern(/^postgresql:\/\//)
    .message('DATABASE_URL 必须以 postgresql:// 开头'),
  DATABASE_SYNC: Joi.boolean().default(false),

  // ===== JWT =====
  // 生产环境的密钥至少 32 字符，这里放宽到 16 字符以便演示
  JWT_SECRET: Joi.string().min(16).required().messages({
    'string.empty': 'JWT_SECRET 不能为空',
    'string.min': 'JWT_SECRET 至少 16 个字符',
    'any.required': 'JWT_SECRET 是必填项',
  }),
  JWT_EXPIRES_IN: Joi.string().default('1h'),
  JWT_REFRESH_EXPIRES_IN: Joi.string().default('7d'),

  // ===== 日志 =====
  LOG_LEVEL: Joi.string()
    .valid('debug', 'verbose', 'log', 'warn', 'error')
    .default('log'),
});
