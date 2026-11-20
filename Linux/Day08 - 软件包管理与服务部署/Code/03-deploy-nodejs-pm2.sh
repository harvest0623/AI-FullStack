#!/bin/bash
# ============================================================
# 文件名：03-deploy-nodejs-pm2.sh
# 用途：演示 Node.js + PM2 部署：nvm 版本管理、PM2 启动/管理、
#       ecosystem.config.js 配置、pm2 startup 开机自启、监控
# 适用：Ubuntu 22.04 LTS
# 场景：电商项目 Node.js 后端部署
# ============================================================

cd "$(dirname "$0")" || exit 1

echo "============================================================"
echo "  Day08 - 03 Node.js + PM2 部署实战"
echo "  服务器：192.168.1.100 / Ubuntu 22.04"
echo "============================================================"

# ---------- 1. nvm 安装与使用 ----------

echo -e "\n[1] nvm 简介"
cat <<'EOF'
nvm (Node Version Manager) 是 Node.js 版本管理工具
优势：
- 不需要 sudo 即可安装 Node.js
- 多版本共存，按项目切换
- 升级简单：nvm install --lts
EOF

echo -e "\n[2] 检查 nvm 是否已安装"
if command -v nvm >/dev/null 2>&1 || [ -s "$HOME/.nvm/nvm.sh" ]; then
    echo "✓ nvm 已安装"
    # 加载 nvm
    [ -s "$HOME/.nvm/nvm.sh" ] && \. "$HOME/.nvm/nvm.sh"
    nvm --version
else
    echo "✗ nvm 未安装"
fi

echo -e "\n[3] 安装 nvm（如未安装）"
cat <<'EOF'
# 安装命令（v0.39.5 是当前稳定版本，可换成最新）
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash

# 或使用国内镜像加速
curl -o- https://gitee.com/mirrors/nvm/raw/v0.39.5/install.sh | bash

# 安装后会自动写入 ~/.bashrc，需重新加载
source ~/.bashrc

# 验证
nvm --version
EOF

echo -e "\n[4] nvm 常用命令"
cat <<'EOF'
nvm install --lts              # 安装最新 LTS 版本
nvm install 20                 # 安装指定版本（20.x 最新）
nvm install 18.19.0            # 安装精确版本
nvm use 20                     # 切换到 20
nvm use --lts                  # 切换到最新 LTS
nvm use default                # 使用默认版本
nvm ls                         # 列出所有已安装版本
nvm ls-remote --lts            # 列出远程所有 LTS 版本
nvm alias default 20           # 设置默认版本
nvm current                    # 查看当前使用版本
nvm run 20 app.js              # 用指定版本运行
nvm exec 20 npm install        # 用指定版本执行 npm
nvm uninstall 18               # 卸载某版本
nvm cache clean                # 清理缓存
EOF

echo -e "\n[5] 国内服务器加速 nvm"
cat <<'EOF'
# 设置 Node.js 下载镜像
export NVM_NODEJS_ORG_MIRROR=https://npmmirror.com/mirrors/node

# 永久写入 ~/.bashrc
echo 'export NVM_NODEJS_ORG_MIRROR=https://npmmirror.com/mirrors/node' >> ~/.bashrc
source ~/.bashrc

# 然后正常安装
nvm install --lts
EOF

echo -e "\n[6] 检查当前 Node.js / npm 版本"
if command -v node >/dev/null 2>&1; then
    echo "命令：node -v && npm -v"
    node -v
    npm -v
    echo ""
    echo "命令：which node && which npm"
    which node
    which npm
else
    echo "Node.js 未安装"
fi

# ---------- 2. npm 镜像源管理 ----------

echo -e "\n[7] npm 镜像源管理（国内服务器推荐）"
if command -v npm >/dev/null 2>&1; then
    echo "命令：npm config get registry"
    npm config get registry
    echo ""
    echo "切换为淘宝镜像："
    echo "npm config set registry https://registry.npmmirror.com"
    echo ""
    echo "切回官方源："
    echo "npm config set registry https://registry.npmjs.org"
else
    echo "npm 未安装"
fi

echo -e "\n[8] nrm —— 镜像源管理工具"
cat <<'EOF'
# 安装
npm install -g nrm

# 查看可用源
nrm ls

# 切换源
nrm use taobao

# 测试速度
nrm test

# 添加自定义源
nrm add company http://npm.company.com/
EOF

# ---------- 3. PM2 安装与基础使用 ----------

echo -e "\n[9] 安装 PM2"
if command -v pm2 >/dev/null 2>&1; then
    echo "✓ PM2 已安装：$(pm2 --version)"
else
    echo "未安装 PM2，安装命令："
    echo "npm install -g pm2"
    echo ""
    echo "国内服务器推荐先切换淘宝源："
    echo "npm config set registry https://registry.npmmirror.com"
    echo "npm install -g pm2"
fi

echo -e "\n[10] PM2 启动应用"
cat <<'EOF'
# 启动单个应用
pm2 start app.js
pm2 start app.js --name "ecommerce-api"
pm2 start ./dist/main.js --name "ecommerce-api"

# 集群模式启动（多进程）
pm2 start app.js -i 4              # 启动 4 个进程
pm2 start app.js -i max            # 用尽所有 CPU 核心
pm2 start app.js -i 0              # 同 max

# 启动 npm 脚本
pm2 start npm --name "ecommerce" -- start
pm2 start npm --name "ecommerce" -- run dev

# 启动 yarn 脚本
pm2 start yarn --name "ecommerce" -- start

# 带参数启动
pm2 start app.js -- --port 3000 --env production

# 启动指定 ecosystem 配置
pm2 start ecosystem.config.js
pm2 start ecosystem.config.js --env production
pm2 start ecosystem.config.js --only ecommerce-api
EOF

# ---------- 4. 实战：用 PM2 启动一个测试应用 ----------

echo -e "\n[11] 实战：创建测试应用并用 PM2 启动"
mkdir -p /tmp/pm2-demo
cat > /tmp/pm2-demo/app.js <<'EOF'
const http = require('http');
const port = process.env.PORT || 3000;
const workerId = process.env.NODE_APP_INSTANCE || 0;

http.createServer((req, res) => {
  res.writeHead(200, {'Content-Type': 'application/json'});
  res.end(JSON.stringify({
    message: 'Hello from PM2 demo',
    worker: workerId,
    timestamp: new Date().toISOString(),
    path: req.url
  }));
}).listen(port, () => {
  console.log(`Worker ${workerId} listening on port ${port}`);
});
EOF

if command -v pm2 >/dev/null 2>&1 && command -v node >/dev/null 2>&1; then
    echo "命令：pm2 start /tmp/pm2-demo/app.js --name demo -i 2"
    pm2 start /tmp/pm2-demo/app.js --name demo -i 2 2>&1 | tail -n 15

    echo -e "\n[12] 验证应用启动"
    sleep 2
    echo "命令：curl -s http://127.0.0.1:3000"
    curl -s http://127.0.0.1:3000
    echo ""
    echo "再请求一次（应该会路由到不同 worker）："
    curl -s http://127.0.0.1:3000
    echo ""
else
    echo "（PM2 或 Node.js 未安装，跳过实战部分）"
fi

# ---------- 5. PM2 进程管理 ----------

echo -e "\n[13] PM2 进程列表"
if command -v pm2 >/dev/null 2>&1; then
    echo "命令：pm2 list"
    pm2 list
fi

echo -e "\n[14] PM2 进程管理命令"
cat <<'EOF'
pm2 list                          # 列出所有进程
pm2 ls                            # 同 list
pm2 status                        # 状态概览

pm2 stop all                      # 停止全部
pm2 stop demo                     # 停止指定
pm2 stop 0                        # 按 ID 停止

pm2 restart all                   # 重启全部
pm2 restart demo                  # 重启指定

pm2 reload all                    # 零停机重启（仅集群模式）
pm2 reload demo                   # 逐个重启 worker，全程不中断

pm2 delete all                    # 删除全部进程
pm2 delete demo                   # 删除指定
pm2 delete 0                      # 按 ID 删除

pm2 describe demo                 # 详细信息
pm2 show demo                     # 同 describe
pm2 info demo                     # 同 describe
EOF

echo -e "\n[15] PM2 重启 vs 重载"
cat <<'EOF'
restart  : 直接杀死所有进程并重新启动，有短暂中断
reload   : 逐个重启 worker，旧 worker 处理完当前请求后退出
           仅 cluster 模式有效，零停机，推荐生产使用
EOF

# ---------- 6. PM2 日志 ----------

echo -e "\n[16] PM2 日志查看"
if command -v pm2 >/dev/null 2>&1; then
    echo "命令：pm2 logs --lines 5 --nostream"
    pm2 logs --lines 5 --nostream 2>&1 | tail -n 15
fi

echo -e "\n[17] PM2 日志命令"
cat <<'EOF'
pm2 logs                          # 所有进程实时日志
pm2 logs demo                     # 指定进程
pm2 logs --lines 200              # 最近 200 行
pm2 logs --err                    # 仅错误日志
pm2 logs --out                    # 仅输出日志
pm2 logs demo --err --lines 50    # demo 进程最近 50 行错误

# 日志文件位置
~/.pm2/logs/
├── demo-out.log                  # 标准输出
├── demo-error.log                # 错误输出
└── ...

# 清空日志
pm2 flush                         # 清空所有
pm2 flush demo                    # 清空指定

# 日志轮转模块（推荐）
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 50M          # 单文件最大 50MB
pm2 set pm2-logrotate:retain 30             # 保留 30 个文件
pm2 set pm2-logrotate:compress true         # 压缩旧日志
EOF

# ---------- 7. PM2 监控 ----------

echo -e "\n[18] PM2 监控命令"
cat <<'EOF'
pm2 monit                         # 实时监控面板（CPU/内存/日志）
pm2 status                        # 状态概览
pm2 describe demo                 # 进程详细信息

# 查看资源占用
pm2 list                          # 看 memory 列
pm2 prettylist                    # 详细 JSON 输出

# 性能分析
pm2 profiler demo                 # CPU 性能分析
pm2 metrics                       # 内置指标
EOF

echo -e "\n[19] PM2 monit 实时监控"
echo "命令：pm2 monit（交互式，按 q 退出）"
echo "上半部分：进程列表（CPU/内存）"
echo "下半部分：日志实时输出"

# ---------- 8. ecosystem.config.js 配置 ----------

echo -e "\n[20] ecosystem.config.js 配置文件（生产推荐）"
cat <<'EOF'
// /opt/ecommerce/backend/ecosystem.config.js
module.exports = {
  apps: [{
    name: 'ecommerce-api',
    script: './dist/main.js',
    instances: 4,                    // 集群实例数（或 'max'）
    exec_mode: 'cluster',            // 集群模式
    cwd: '/opt/ecommerce/backend',

    // 环境变量
    env: {
      NODE_ENV: 'development',
      PORT: 3000
    },
    env_production: {
      NODE_ENV: 'production',
      PORT: 3000
    },
    env_staging: {
      NODE_ENV: 'staging',
      PORT: 3001
    },

    // 资源控制
    max_memory_restart: '1G',        // 内存超 1G 自动重启
    node_args: '--max-old-space-size=1024',  // Node.js V8 参数

    // 日志
    error_file: '/opt/ecommerce/logs/err.log',
    out_file: '/opt/ecommerce/logs/out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss',
    merge_logs: true,                // 合并日志（集群模式）

    // 重启策略
    autorestart: true,               // 异常退出自动重启
    watch: false,                    // 文件变化自动重启（开发用）
    ignore_watch: ['node_modules', 'logs', 'dist'],

    // 优雅停止
    kill_timeout: 3000,              // SIGTERM 后等多久发 SIGKILL
    listen_timeout: 5000,            // 启动超时
  }]
};
EOF

echo -e "\n[21] 用 ecosystem 启动应用"
cat <<'EOF'
# 启动（默认 env）
pm2 start ecosystem.config.js

# 启动生产环境
pm2 start ecosystem.config.js --env production

# 重启
pm2 restart ecosystem.config.js --env production

# 重载
pm2 reload ecosystem.config.js

# 删除
pm2 delete ecosystem.config.js
EOF

# ---------- 9. PM2 开机自启 ----------

echo -e "\n[19] PM2 开机自启配置（重要！）"
cat <<'EOF'
# 1. 生成开机自启脚本
pm2 startup

# 输出会提示执行类似下面命令（不同系统不同）：
sudo env PATH=$PATH:$(dirname $(which node)) \
  $(which pm2) startup systemd -u deploy --hp /home/deploy

# 2. 保存当前进程列表（重要！重启后自动恢复）
pm2 save

# 3. 验证（生成的 systemd 服务）
systemctl status pm2-deploy

# 流程总结：
# pm2 startup → 生成 systemd 服务（pm2-deploy.service）
# pm2 save    → 保存进程列表到 ~/.pm2/dump.pm2
# 系统启动 → systemd 启动 pm2-deploy → PM2 读取 dump.pm2 恢复所有进程
EOF

echo -e "\n[20] PM2 开机自启完整流程（实战）"
cat <<'EOF'
# 1. 启动所有应用
pm2 start ecosystem.config.js --env production

# 2. 生成 systemd 启动脚本（按提示执行 sudo 命令）
pm2 startup systemd

# 假设提示执行：
sudo env PATH=$PATH:/home/deploy/.nvm/versions/node/v20.10.0/bin \
  /home/deploy/.nvm/versions/node/v20.10.0/bin/pm2 \
  startup systemd -u deploy --hp /home/deploy

# 3. 保存当前进程列表
pm2 save

# 4. 测试：重启服务器
sudo reboot

# 5. SSH 重新登录后验证
pm2 list
# 应该看到所有进程自动启动
EOF

# ---------- 10. 清理演示 ----------

echo -e "\n[21] 清理本脚本创建的演示进程"
if command -v pm2 >/dev/null 2>&1; then
    echo "命令：pm2 delete demo"
    pm2 delete demo 2>/dev/null && echo "已删除 demo 进程" || echo "（无 demo 进程）"
    pm2 save 2>/dev/null
fi
rm -rf /tmp/pm2-demo

# ---------- 11. 完整部署流程 ----------

echo -e "\n[22] Node.js + PM2 完整部署流程"
cat <<'EOF'
# 1. 安装 nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
source ~/.bashrc

# 2. 设置镜像加速（国内服务器）
export NVM_NODEJS_ORG_MIRROR=https://npmmirror.com/mirrors/node

# 3. 安装 Node.js LTS
nvm install --lts
nvm alias default lts/iron    # 设置默认版本

# 4. 配置 npm 镜像
npm config set registry https://registry.npmmirror.com

# 5. 安装 PM2
npm install -g pm2

# 6. 部署代码（假设已上传到 /opt/ecommerce/backend）
cd /opt/ecommerce/backend

# 7. 安装依赖
npm install --production

# 8. 构建
npm run build

# 9. 创建 ecosystem 配置
cat > ecosystem.config.js <<'CONF'
module.exports = {
  apps: [{
    name: 'ecommerce-api',
    script: './dist/main.js',
    instances: 4,
    exec_mode: 'cluster',
    cwd: '/opt/ecommerce/backend',
    env: { NODE_ENV: 'production', PORT: 3000 },
    max_memory_restart: '1G',
    error_file: '/opt/ecommerce/logs/err.log',
    out_file: '/opt/ecommerce/logs/out.log',
  }]
};
CONF

# 10. 启动
mkdir -p /opt/ecommerce/logs
pm2 start ecosystem.config.js --env production

# 11. 开机自启
pm2 startup systemd
# 按提示执行 sudo 命令
pm2 save

# 12. 验证
pm2 list
pm2 logs --lines 20
curl http://127.0.0.1:3000/api/health
EOF

echo -e "\n============================================================"
echo "  Day08 - 03 Node.js + PM2 部署实战 完成"
echo "============================================================"
