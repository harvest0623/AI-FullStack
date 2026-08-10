import { Injectable, ConflictException } from '@nestjs/common';
import * as bcrypt from 'bcrypt';
import { User, toSafeUser, SafeUser } from './user.entity';
import { RegisterUserDto } from './dto/register-user.dto';

/**
 * UsersService —— 用户 CRUD + 密码哈希
 *
 * 本章用内存数组模拟数据库表，关注点有三：
 *
 * 1. 密码哈希（bcrypt）
 *    - bcrypt 内置 salt + 慢哈希，抵御彩虹表与暴力破解
 *    - saltRounds = 10 是社区共识的最低门槛，生产建议 12
 *    - 哈希结果自带 salt 与版本信息，校验时无需单独存 salt
 *
 * 2. 用户唯一性
 *    - 注册前必须先 findByUsername 检查冲突，避免重复账号
 *
 * 3. 对外安全形状
 *    - 任何返回给上层（controller / JWT payload）的 user 都用 toSafeUser 剥离 password
 *
 * 为什么不用 MD5 / SHA256？
 *   - MD5/SHA 是「快哈希」，专为文件校验设计，GPU 每秒可算千万次
 *   - bcrypt 是「慢哈希」，每次计算有故意延迟，让暴力破解不可行
 *   - bcrypt 还自动加盐，无需在数据库单独维护 salt 字段
 */

/** bcrypt salt rounds：哈希迭代次数，2^saltRounds 次
 *  - 10 → 约 60ms / 次（开发演示足够）
 *  - 12 → 约 250ms / 次（生产推荐）
 *  每增加 1，时间翻倍。 */
const BCRYPT_SALT_ROUNDS = 10;

/** 角色 → 默认权限映射，演示 RBAC0 的「角色含权限」语义 */
const ROLE_PERMISSIONS: Record<string, string[]> = {
  admin: ['article:read', 'article:create', 'article:update', 'article:delete', 'user:manage'],
  editor: ['article:read', 'article:create', 'article:update'],
  visitor: ['article:read'],
};

@Injectable()
export class UsersService {
  /** 内存「用户表」，启动后初始化一个 admin 账号方便测试 */
  private readonly users: User[] = [];
  private nextId = 1;

  constructor() {
    this.seedAdmin();
  }

  /**
   * 初始化内置 admin 账号，方便启动后立即测试受保护接口。
   * 真实项目应通过 migration / seed 脚本完成。
   */
  private async seedAdmin(): Promise<void> {
    const password = await bcrypt.hash('admin123', BCRYPT_SALT_ROUNDS);
    this.users.push({
      id: this.nextId++,
      username: 'admin',
      password,
      roles: ['admin'],
      permissions: ROLE_PERMISSIONS['admin'],
      createdAt: Date.now(),
    });
  }

  /**
   * 注册新用户。
   *
   * @returns SafeUser 不含 password
   * @throws ConflictException 用户名已存在
   */
  async create(dto: RegisterUserDto): Promise<SafeUser> {
    // ① 唯一性校验
    const exists = this.findByUsername(dto.username);
    if (exists) {
      throw new ConflictException(`用户名 ${dto.username} 已被占用`);
    }

    // ② 密码哈希
    const hashed = await bcrypt.hash(dto.password, BCRYPT_SALT_ROUNDS);

    // ③ 角色与权限摊平
    const roles = dto.roles?.length ? dto.roles : ['visitor'];
    const permissions = [
      ...new Set(roles.flatMap((r) => ROLE_PERMISSIONS[r] ?? [])),
    ];

    // ④ 入「库」
    const user: User = {
      id: this.nextId++,
      username: dto.username,
      password: hashed,
      roles,
      permissions,
      createdAt: Date.now(),
    };
    this.users.push(user);

    return toSafeUser(user);
  }

  /**
   * 按用户名查询完整 User（含 password 哈希）。
   * 仅供 AuthService / LocalStrategy 内部使用，**不**暴露给控制器。
   */
  findByUsername(username: string): User | undefined {
    return this.users.find((u) => u.username === username);
  }

  /** 按 id 查询完整 User */
  findById(id: number): User | undefined {
    return this.users.find((u) => u.id === id);
  }

  /**
   * 用 bcrypt 比对明文密码与哈希。
   *
   * bcrypt.compare 内部会从 hashed 字符串里解析出 salt 与算法版本，
   * 用相同 salt 重新哈希 plain，再比对两个哈希是否一致。
   * 因此我们无需在数据库里单独存 salt 字段。
   *
   * @returns true / false（密码正确 / 错误），不抛异常，由调用方决定语义
   */
  async validatePassword(plain: string, hashed: string): Promise<boolean> {
    return bcrypt.compare(plain, hashed);
  }

  /** 列出所有用户（剥离 password） */
  list(): SafeUser[] {
    return this.users.map(toSafeUser);
  }
}
