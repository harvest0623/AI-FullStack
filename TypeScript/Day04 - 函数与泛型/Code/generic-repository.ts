/**
 * Day04 - 函数与泛型
 * generic-repository.ts：泛型 Repository 模式预览（为 NestJS / TypeORM 铺垫）
 *
 * 运行：npx ts-node generic-repository.ts
 *
 * 这是 NestJS + TypeORM 中 Repository<T> 模式的最小可运行原型，
 * 真实场景中 save/find 会落库（MongoDB / MySQL），这里用内存 Map 模拟。
 */
export {};

// ============================================================
// 1. 基础类型：实体接口与 ID 类型
// ============================================================

// 所有实体都有 id（约定字段）
interface Entity {
  id: string | number;
}

// 业务实体示例：User / Post
interface User extends Entity {
  id: number;
  name: string;
  email: string;
}

interface Post extends Entity {
  id: string;
  title: string;
  authorId: number;
  published: boolean;
}

// ============================================================
// 2. 泛型 Repository 接口
// ============================================================

// 仓储模式的核心契约：CRUD + 列表查询
//   T 约束为 Entity，保证每个实体都有 id 字段
interface IRepository<T extends Entity> {
  save(entity: T): Promise<T>;
  findById(id: T['id']): Promise<T | null>;
  find(predicate?: (entity: T) => boolean): Promise<T[]>;
  delete(id: T['id']): Promise<boolean>;
  count(): Promise<number>;
}

// ============================================================
// 3. 内存仓储实现：用 Map 模拟数据库
// ============================================================

class InMemoryRepository<T extends Entity> implements IRepository<T> {
  // Map 的键类型与实体 id 类型对齐：T['id'] 是索引访问类型
  private storage = new Map<T['id'], T>();

  async save(entity: T): Promise<T> {
    // 真实场景：INSERT or UPDATE
    this.storage.set(entity.id, entity);
    return entity;
  }

  async findById(id: T['id']): Promise<T | null> {
    return this.storage.get(id) ?? null;
  }

  async find(predicate?: (entity: T) => boolean): Promise<T[]> {
    const all = Array.from(this.storage.values());
    if (!predicate) return all;
    return all.filter(predicate);
  }

  async delete(id: T['id']): Promise<boolean> {
    return this.storage.delete(id);
  }

  async count(): Promise<number> {
    return this.storage.size;
  }
}

// ============================================================
// 4. 用法：创建两个具体仓储
// ============================================================

async function main() {
  console.log('--- 4. 用法演示 ---');

  // 4.1 User 仓储
  const userRepo: IRepository<User> = new InMemoryRepository<User>();

  await userRepo.save({ id: 1, name: 'Alice', email: 'alice@x.com' });
  await userRepo.save({ id: 2, name: 'Bob', email: 'bob@x.com' });
  await userRepo.save({ id: 3, name: 'Carol', email: 'carol@x.com' });

  const alice = await userRepo.findById(1);
  console.log('userRepo.findById(1) =', alice);

  const bob = await userRepo.find((u) => u.name.startsWith('B'));
  console.log('userRepo.find(name startswith B) =', bob);

  console.log('userRepo.count() =', await userRepo.count());

  // 4.2 Post 仓储：注意 id 类型为 string
  const postRepo: IRepository<Post> = new InMemoryRepository<Post>();

  await postRepo.save({ id: 'p001', title: 'Hello TS', authorId: 1, published: true });
  await postRepo.save({ id: 'p002', title: 'Generics Deep Dive', authorId: 1, published: false });
  await postRepo.save({ id: 'p003', title: 'Node.js Notes', authorId: 2, published: true });

  const publishedPosts = await postRepo.find((p) => p.published);
  console.log('\npostRepo.find(published) =', publishedPosts);

  const alicePosts = await postRepo.find((p) => p.authorId === 1);
  console.log('postRepo.find(authorId=1) =', alicePosts);

  const deleted = await postRepo.delete('p003');
  console.log('postRepo.delete("p003") =', deleted);
  console.log('postRepo.count() after delete =', await postRepo.count());

  // ============================================================
  // 5. 泛型 + keyof：类型安全的"按字段查询"
  // ============================================================

  console.log('\n--- 5. 按 keyof 查询 ---');

  // 扩展 Repository：增加 findBy(field, value) 方法
  //   K extends keyof T：field 必须是实体某个键
  //   T[K]：该键对应的值类型
  class QueryableRepository<T extends Entity> extends InMemoryRepository<T> {
    async findBy<K extends keyof T>(field: K, value: T[K]): Promise<T[]> {
      const all = await this.find();
      return all.filter((e) => e[field] === value);
    }
  }

  const queryableUserRepo = new QueryableRepository<User>();
  await queryableUserRepo.save({ id: 10, name: 'Dave', email: 'dave@x.com' });
  await queryableUserRepo.save({ id: 11, name: 'Eve', email: 'eve@x.com' });
  await queryableUserRepo.save({ id: 12, name: 'Dave', email: 'dave2@x.com' });

  // 类型安全：field 必须是 User 的键，value 必须匹配该键的类型
  const daves = await queryableUserRepo.findBy('name', 'Dave');
  console.log('findBy("name", "Dave") =', daves);

  // findById 字段对应 number，传字符串会报错（注释取消可验证）
  // queryableUserRepo.findBy('id', 'not-a-number'); // ❌ 类型错误

  // ============================================================
  // 6. 装饰器风格的依赖注入预告（为 NestJS 铺垫）
  // ============================================================

  console.log('\n--- 6. 依赖注入预告 ---');

  // NestJS 的 @InjectRepository(User) 本质就是：
  //   const repo: Repository<User> = someFactory.create(User);
  // 注意：entityClass 此处只用于取 .name，不要求它本身实现 Entity；
  //   T（实体类型）由调用方通过 repo 参数显式传入。
  class RepositoryRegistry {
    private repos = new Map<string, IRepository<any>>();

    // 用 { name: string } 约束：任何 class 构造器都自带 name 属性
    register<T extends Entity>(
      entityClass: { new (...args: unknown[]): unknown; name: string },
      repo: IRepository<T>
    ): void {
      this.repos.set(entityClass.name, repo);
    }

    resolve<T extends Entity>(entityClass: { new (...args: unknown[]): unknown; name: string }): IRepository<T> | undefined {
      // 运行时按 name 取回；类型层面由调用方负责保证一致（NestJS 用装饰器元数据保证）
      return this.repos.get(entityClass.name) as IRepository<T> | undefined;
    }
  }

  // 模拟 User / Post 类（NestJS 中是真实 Entity 类）
  class UserEntity {}
  class PostEntity {}

  const registry = new RepositoryRegistry();
  registry.register(UserEntity, new InMemoryRepository<User>());
  registry.register(PostEntity, new InMemoryRepository<Post>());

  const injectedUserRepo = registry.resolve<User>(UserEntity);
  if (injectedUserRepo) {
    await injectedUserRepo.save({ id: 100, name: 'Injected', email: 'i@x.com' });
    console.log('注入的 User 仓储查到 =', await injectedUserRepo.findById(100));
  }

  console.log('\n[generic-repository.ts] 全部示例执行完毕。');
}

main().catch((err) => {
  console.error('Error:', err);
  process.exit(1);
});
