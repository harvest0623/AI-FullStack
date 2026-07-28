/**
 * Day17 - mongoose Schema 与 Model 定义
 *
 * mongoose 三层架构：
 *   1. Connection（连接）：mongoose.connect(uri) 建立到 MongoDB 的连接，全局单例
 *   2. Schema（模式）：定义文档结构 —— 字段名、类型、校验规则、索引、钩子
 *   3. Model（模型）：由 Schema 编译而成，是操作集合的类，提供 CRUD 静态方法
 *
 * 关系类比：
 *   MySQL Table  ↔  MongoDB Collection  ↔  mongoose Model
 *   MySQL Row    ↔  MongoDB Document    ↔  mongoose Document（Model 实例）
 *   MySQL Column ↔  MongoDB Field       ↔  Schema 字段
 *
 * 本文件只“定义”模型，不连接数据库，便于被其他模块复用。
 * 运行环境准备见 mongoose-crud.js / server.js 顶部注释。
 */

const mongoose = require('mongoose');

const { Schema } = mongoose;

// ---------------------------------------------------------------------------
// 1. User Schema
// ---------------------------------------------------------------------------
// Schema 定义了字段类型、必填、默认值、自定义校验、索引、时间戳
const userSchema = new Schema(
  {
    // 字段类型：String / Number / Date / Boolean / ObjectId / Array / Mixed / Map
    username: {
      type: String,
      required: [true, '用户名必填'], // required 可带自定义错误信息
      unique: true, // 唯一索引（mongoose 会创建 unique index）
      trim: true, // 自动去除首尾空白
      minlength: 3,
      maxlength: 30,
    },
    email: {
      type: String,
      required: true,
      lowercase: true, // 自动转小写
      // 简单正则校验（生产环境建议用更严谨的库）
      match: [/^[\w.+-]+@[\w-]+\.[\w.-]+$/, '邮箱格式不正确'],
      index: true, // 普通索引，加速按邮箱查询
    },
    role: {
      type: String,
      enum: ['admin', 'editor', 'viewer'], // 枚举校验
      default: 'viewer',
    },
    // 自定义校验器：validator 返回 false 则抛出 message
    age: {
      type: Number,
      default: null,
      validate: {
        validator: (v) => v === null || (v >= 0 && v <= 150),
        message: '年龄必须在 0~150 之间',
      },
    },
  },
  {
    // timestamps: true 自动添加 createdAt 与 updatedAt 两个 Date 字段
    //   - 创建文档时 createdAt = updatedAt = now
    //   - 每次更新时 updatedAt 自动刷新
    // 对应 MySQL 的 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    //           与 updated_at TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    timestamps: true,
    // 严格模式：未在 Schema 中声明的字段不会被保存（防止脏数据）
    strict: true,
  }
);

// 虚拟字段：不存入数据库，按需计算
userSchema.virtual('profile').get(function () {
  return `${this.username} (${this.role})`;
});

// 实例方法：操作单个文档
userSchema.methods.isAdmin = function () {
  return this.role === 'admin';
};

// 静态方法：操作整个集合
userSchema.statics.findByEmail = function (email) {
  return this.findOne({ email: email.toLowerCase() });
};

// 编译为 Model：mongoose.model('模型名', schema)
//   - 第三个参数可指定集合名，省略时自动复数小写：User → users
const User = mongoose.model('User', userSchema);

// ---------------------------------------------------------------------------
// 2. Article Schema（带与 User 的关联）
// ---------------------------------------------------------------------------
const articleSchema = new Schema(
  {
    title: {
      type: String,
      required: [true, '标题必填'],
      trim: true,
      maxlength: 200,
      // 文本索引（适合搜索；生产环境大规模搜索建议用 Elasticsearch/向量库）
      index: 'text',
    },
    content: {
      type: String,
      default: '',
    },
    // 关联：存的是 User 的 _id（ObjectId）
    author: {
      type: Schema.Types.ObjectId,
      ref: 'User', // 指向 User 模型，populate 时据此联表
      required: true,
      index: true,
    },
    tags: {
      type: [String], // 数组类型，每个元素是 String
      default: [],
      // 数组元素也可加索引：Mongoose 会为 tags 字段建多键索引
    },
    viewCount: {
      type: Number,
      default: 0,
      min: 0,
    },
    // 软删除标记：deleted=true 视为已删除，但不真正移除文档
    deleted: {
      type: Boolean,
      default: false,
      index: true,
    },
  },
  {
    timestamps: true, // createdAt / updatedAt
    toJSON: { virtuals: true }, // 转 JSON 时包含虚拟字段
    toObject: { virtuals: true },
  }
);

// 文档中间件（pre hook）：保存前打印日志
articleSchema.pre('save', function (next) {
  if (this.isNew) {
    console.log(`[Article] 即将创建文章: ${this.title}`);
  }
  next();
});

// 查询中间件：默认排除软删除的文档
//   之后所有 find/findOne 等会自动带上 deleted: { $ne: true } 过滤
articleSchema.pre(/^find/, function (next) {
  // 仅当查询未显式指定 deleted 时才自动过滤，避免覆盖特殊查询
  if (this.getQuery().deleted === undefined) {
    this.where({ deleted: { $ne: true } });
  }
  next();
});

const Article = mongoose.model('Article', articleSchema);

// ---------------------------------------------------------------------------
// 导出：供 mongoose-crud.js / repository-pattern.js / server.js 复用
// ---------------------------------------------------------------------------
module.exports = { mongoose, User, Article };
