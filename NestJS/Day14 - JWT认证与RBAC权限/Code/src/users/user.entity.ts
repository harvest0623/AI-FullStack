/**
 * User 实体（内存模拟数据库版本）
 *
 * 真实项目里这应当对应数据库表（TypeORM / Prisma / Mongoose），
 * 本章为聚焦认证流程，用纯 TypeScript 类 + 内存数组模拟。
 *
 * 关键字段说明：
 *   - password：bcrypt 哈希后的字符串，**绝不**保存明文，也**绝不**返回给客户端
 *   - roles：RBAC0 中的「角色」层，决定用户能访问哪类资源（粗粒度）
 *   - permissions：RBAC0 中的「权限」层，决定用户能执行的具体操作（细粒度）
 *
 * 「角色」与「权限」的关系：
 *   角色是权限的集合（admin 拥有所有权限），
 *   生产实践里通常「角色 → 权限」由数据库表配置，登录后把权限摊平到 JWT。
 *   这里为简化演示，角色与权限都直接存在 user 上。
 */

/**
 * RBAC0 三层模型：
 *   用户（User） → 角色（Role） → 权限（Permission）
 *
 * 用户被赋予若干角色，角色包含若干权限，
 * 守卫校验时既可基于角色（@Roles('admin')），也可基于权限（@Permissions('article:create')）。
 */
export interface User {
  /** 用户唯一 ID（自增） */
  id: number;

  /** 登录用户名，唯一 */
  username: string;

  /** bcrypt 哈希后的密码，禁止明文存储与外泄 */
  password: string;

  /** RBAC0 角色集合，如 ['admin']、['editor', 'visitor'] */
  roles: string[];

  /** RBAC0 权限集合，比角色更细粒度，如 ['article:create', 'article:delete'] */
  permissions: string[];

  /** 创建时间戳（ms） */
  createdAt: number;
}

/**
 * 对外暴露的安全形状：剥离 password 字段。
 *
 * 任何从 service 返回给 controller / 客户端的 user 都应先经过 toSafeUser 转换，
 * 避免 bcrypt 哈希意外泄露（即便哈希也无法逆推原文，但仍是攻击者爆破密码的素材）。
 */
export type SafeUser = Omit<User, 'password'>;

/** 把 User 转为 SafeUser（剥离 password） */
export function toSafeUser(user: User): SafeUser {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { password, ...rest } = user;
  return rest;
}
