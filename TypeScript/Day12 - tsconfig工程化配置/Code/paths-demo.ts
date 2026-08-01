/**
 * paths-demo.ts —— 路径别名配置实战
 *
 * 搭配 tsconfig.dev.json / tsconfig.prod.json 中的 paths 字段：
 *   "baseUrl": ".",
 *   "paths": {
 *     "@/*":        ["src/*"],
 *     "@config/*":  ["src/config/*"],
 *     "@utils/*":   ["src/utils/*"]
 *   }
 *
 * 运行时解析说明：
 *   1. tsc 编译：仅做类型检查，产物 JS 中仍然保留 require('@utils/logger')
 *      这种别名路径，Node 原生无法解析，会抛 MODULE_NOT_FOUND。
 *   2. ts-node 运行：通过 tsconfig 中的 paths 配置，ts-node 内置的
 *      paths 解析器可在运行时把别名映射到真实文件（见 package.json
 *      的 run:paths 脚本，使用 ts-node -T）。
 *   3. 编译产物运行：必须借助 tsc-alias（见 build:alias 脚本）或
 *      tsconfig-paths、bundler（esbuild/webpack/vite）在打包阶段把
 *      别名替换为相对路径。
 */

// ═══════════════════════════════════════════════════════════════
// 1. 相对路径的痛点（被别名替代前的写法）
// ═══════════════════════════════════════════════════════════════
// 假设目录结构：
//   src/
//     config/index.ts
//     utils/logger.ts
//     utils/format.ts
//     services/user.service.ts   <-- 想引用 config 和 utils
//
// 在 user.service.ts 中使用相对路径：
//   import { config } from '../../config';           // 层级深、易错
//   import { logger } from '../../utils/logger';     // 移动文件即失效
//   import { format } from '../../utils/format';

// ═══════════════════════════════════════════════════════════════
// 2. 使用 @/* 别名后的写法（推荐）
// ═══════════════════════════════════════════════════════════════
//   import { config } from '@config/index';
//   import { logger } from '@utils/logger';
//   import { format } from '@utils/format';
//
// 文件移动时无需调整 import 路径；IDE 跳转、补全均可正常工作。

// ═══════════════════════════════════════════════════════════════
// 3. 模拟实现（因本文件位于 Code 根目录而非 src/，这里用相对路径
//    真实演示 paths 字段是如何映射的；落地到项目时请放 src/ 下）
// ═══════════════════════════════════════════════════════════════

// 模拟 src/config/index.ts 的内容
namespace DemoConfig {
  export interface AppConfig {
    readonly env: 'dev' | 'prod';
    readonly port: number;
    readonly logLevel: 'debug' | 'info' | 'warn' | 'error';
  }

  export const config: AppConfig = {
    env: 'dev',
    port: 3000,
    logLevel: 'info',
  };
}

// 模拟 src/utils/logger.ts 的内容
namespace DemoLogger {
  export function info(msg: string, ctx?: Record<string, unknown>): void {
    const time = new Date().toISOString();
    const payload = ctx ? ` ${JSON.stringify(ctx)}` : '';
    console.log(`[INFO ][${time}] ${msg}${payload}`);
  }

  export function error(msg: string, err?: unknown): void {
    const time = new Date().toISOString();
    // useUnknownInCatchVariables 风格：err 是 unknown，需先收窄
    const detail = err instanceof Error ? err.stack : String(err);
    console.error(`[ERROR][${time}] ${msg}\n${detail ?? ''}`);
  }
}

// 模拟 src/utils/format.ts 的内容
namespace DemoFormat {
  export function pretty(obj: Record<string, unknown>): string {
    return JSON.stringify(obj, null, 2);
  }
}

// ═══════════════════════════════════════════════════════════════
// 4. 业务代码：用别名引用上述模块（此处用命名空间模拟）
//    在真实项目中：import { config } from '@config';
//                  import { logger, format } from '@utils';
// ═══════════════════════════════════════════════════════════════
function bootstrap(): void {
  const { config } = DemoConfig;
  const { info, error } = DemoLogger;
  const { pretty } = DemoFormat;

  info('应用启动', { env: config.env, port: config.port });
  console.log('当前配置：\n' + pretty(config as unknown as Record<string, unknown>));

  try {
    // strictNullChecks + noUncheckedIndexedAccess 风格的演示
    const levels: Array<'debug' | 'info' | 'warn' | 'error'> = ['debug', 'info', 'warn', 'error'];
    const pick = levels[Math.floor(Math.random() * levels.length)];
    if (pick === undefined) {
      throw new Error('随机取值异常');
    }
    info(`随机日志级别：${pick}`);
  } catch (e) {
    // useUnknownInCatchVariables：e 是 unknown，必须收窄
    error('启动过程中捕获异常', e);
  }
}

bootstrap();

// ═══════════════════════════════════════════════════════════════
// 5. 运行方式速查
// ═══════════════════════════════════════════════════════════════
// 开发期（ts-node 直接跑源码）：
//   npm run run:paths        # ts-node -T paths-demo.ts
//   ts-node 会读取 tsconfig.dev.json 的 paths 字段并在运行时解析
//
// 生产构建（tsc + tsc-alias）：
//   npm run build:alias      # tsc -p tsconfig.prod.json && tsc-alias -p tsconfig.prod.json
//   tsc-alias 会扫描 dist/prod/**/*.js，把 require('@/utils/logger')
//   替换为相对路径 require('../utils/logger')
//
// bundler 场景（webpack / esbuild / vite）：
//   各 bundler 需在自身配置中注册 alias：
//     webpack:  resolve.alias['@'] = path.resolve(__dirname, 'src')
//     vite:     resolve.alias['@'] = path.resolve(__dirname, 'src')
//     esbuild:  plugins: [alias({ '@': './src' })]
//   bundler 替换后产物 JS 中即为相对路径，无需 tsc-alias
