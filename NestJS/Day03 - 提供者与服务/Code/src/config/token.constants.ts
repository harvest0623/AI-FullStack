// ============================================================
// Provider Token 常量定义
// ------------------------------------------------------------
// 字符串 Token 与 Symbol Token 都需要 @Inject 装饰器来注入。
// 将 Token 集中管理，避免散落在各处的魔法字符串导致命名冲突。
// ============================================================

// ------------------------------------------------------------
// 字符串 Token
// ------------------------------------------------------------

// useValue 注册的配置对象（被 ArticlesService 消费）
export const CONFIG_TOKEN = 'CONFIG';

// useFactory 注册的数据库连接（被 ArticlesService 消费）
export const DATABASE_CONNECTION_TOKEN = 'DATABASE_CONNECTION';

// useValue 注册的 mock 对象（演示值提供者）
export const MOCK_SENDER_TOKEN = 'MOCK_SENDER';

// useFactory 注册的缓存客户端（演示工厂提供者）
export const CACHE_CLIENT_TOKEN = 'CACHE_CLIENT';

// useExisting 别名 Token（演示别名提供者，指向 NotificationSender）
export const SENDER_ALIAS_TOKEN = 'SENDER_ALIAS';

// ------------------------------------------------------------
// Symbol Token
// ------------------------------------------------------------
// Symbol 全局唯一，从根本上避免字符串 Token 命名冲突
export const APP_INFO_TOKEN = Symbol('APP_INFO');
