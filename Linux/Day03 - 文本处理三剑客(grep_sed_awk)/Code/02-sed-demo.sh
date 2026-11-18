#!/bin/bash
# 文件用途：sed 流编辑器演示
#           演示替换 s、删除 d、追加 a、插入 i、打印 p、-i 原地修改
#           批量替换配置文件、删除空行和注释行
# 适用系统：Ubuntu 22.04 LTS（及更高版本）
# 执行方式：bash 02-sed-demo.sh
# 作者：AI-FullStack

# ============================================================
# 脚本说明：
#   本脚本先创建模拟的配置文件与文本文件，
#   然后用 sed 的各种命令进行编辑演示。
#   脚本可重复执行。
# ============================================================

# 工作目录
WORK_DIR="/tmp/sed-demo"

echo "================================================"
echo "  sed 流编辑器演示"
echo "  工作目录：$WORK_DIR"
echo "================================================"

# === 0. 创建模拟素材 ===
echo ""
echo ">>> [0] 创建模拟配置文件与文本素材..."

rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

# 创建 Nginx 配置文件
cat > "$WORK_DIR/nginx.conf" <<'EOF'
# Nginx 配置文件
# 作者：运维团队
# 更新：2026-07-29

worker_processes auto;
pid /run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    # 基础设置
    sendfile on;
    tcp_nopush on;
    keepalive_timeout 65;

    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] '
                    '"$request" $status $body_bytes_sent';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    # 电商项目服务
    server {
        listen 80;
        server_name example.com www.example.com;

        root /var/www/ecommerce;
        index index.html index.htm;

        location / {
            try_files $uri $uri/ =404;
        }

        location /api/ {
            proxy_pass http://localhost:3000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /static/ {
            root /var/www/ecommerce;
            expires 30d;
        }
    }
}
EOF

# 创建应用配置文件
cat > "$WORK_DIR/app.conf" <<'EOF'
# Application Configuration
# Database settings
db_host=localhost
db_port=3306
db_user=ecommerce_user
db_password=OldPassword123
db_name=ecommerce

# Redis settings
redis_host=localhost
redis_port=6379
redis_password=OldRedisPass

# Application settings
app_port=3000
app_env=development
debug=true
log_level=debug

# 以下为空行测试


# 上面有空行
EOF

# 创建带 Windows 换行符的文件
printf "line1\r\nline2\r\nline3\r\n" > "$WORK_DIR/windows-file.txt"

# 创建一个普通文本文件
cat > "$WORK_DIR/sample.txt" <<'EOF'
Hello World
Hello Linux
Hello Shell
Hello Sed
World Hello
Linux is awesome
Sed is powerful
EOF

echo "    模拟素材已创建："
ls -la "$WORK_DIR/"

# === 1. sed 替换命令 s ===
echo ""
echo ">>> [1] sed 替换命令 s（substitute）..."

echo "---- sed 's/Hello/Hi/' sample.txt（每行第一个 Hello 替换为 Hi）----"
sed "s/Hello/Hi/" "$WORK_DIR/sample.txt"

echo ""
echo "---- sed 's/Hello/Hi/g' sample.txt（全局替换，每行所有 Hello）----"
sed "s/Hello/Hi/g" "$WORK_DIR/sample.txt"

echo ""
echo "---- sed 's/Hello/Hi/2' sample.txt（仅替换每行第 2 个 Hello）----"
sed "s/Hello/Hi/2" "$WORK_DIR/sample.txt"

echo ""
echo "---- sed 's/hello/Hi/gi' sample.txt（忽略大小写全局替换）----"
sed "s/hello/Hi/gi" "$WORK_DIR/sample.txt"

echo ""
echo "---- sed 's/Hello/Hi/gp' sample.txt（替换并打印，需 -n）----"
sed -n "s/Hello/Hi/gp" "$WORK_DIR/sample.txt"

echo ""
echo "---- sed 's/World/&Wide/' sample.txt（& 引用匹配内容）----"
sed "s/World/&Wide/" "$WORK_DIR/sample.txt"

echo ""
echo "---- sed -E 's/(Hello) (World)/\2 \1/' sample.txt（交换两个单词）----"
sed -E "s/(Hello) (World)/\2 \1/" "$WORK_DIR/sample.txt"

# === 2. sed 不同分隔符 ===
echo ""
echo ">>> [2] sed 不同分隔符（避免转义 /）..."

echo "---- sed 's/\/var\/www/\/opt\/ecommerce/' nginx.conf（路径替换，需转义）----"
sed "s/\/var\/www/\/opt\/ecommerce/g" "$WORK_DIR/nginx.conf" | grep "root"

echo ""
echo "---- sed 's|/var/www|/opt/ecommerce|g' nginx.conf（用 | 作分隔符，更清晰）----"
sed "s|/var/www|/opt/ecommerce|g" "$WORK_DIR/nginx.conf" | grep "root"

echo ""
echo "---- sed 's#/var/log/nginx#/opt/ecommerce/logs/nginx#g' nginx.conf（用 # 作分隔符）----"
sed "s#/var/log/nginx#/opt/ecommerce/logs/nginx#g" "$WORK_DIR/nginx.conf" | grep "log"

# === 3. sed 删除命令 d ===
echo ""
echo ">>> [3] sed 删除命令 d（delete）..."

echo "---- sed '1d' sample.txt（删除第 1 行）----"
sed "1d" "$WORK_DIR/sample.txt"

echo ""
echo "---- sed '1,3d' sample.txt（删除第 1-3 行）----"
sed "1,3d" "$WORK_DIR/sample.txt"

echo ""
echo "---- sed '\$d' sample.txt（删除最后一行）----"
sed '$d' "$WORK_DIR/sample.txt"

echo ""
echo "---- sed '/Hello/d' sample.txt（删除含 Hello 的行）----"
sed "/Hello/d" "$WORK_DIR/sample.txt"

echo ""
echo "---- sed '/^$/d' app.conf（删除空行）----"
sed "/^$/d" "$WORK_DIR/app.conf"

echo ""
echo "---- sed '/^#/d' app.conf（删除注释行）----"
sed "/^#/d" "$WORK_DIR/app.conf"

echo ""
echo "---- sed '/^#\|^$/d' app.conf（删除注释行和空行）----"
sed "/^#\|^$/d" "$WORK_DIR/app.conf"

echo ""
echo "---- sed '/^#\|^$/d; /^$/d' app.conf（多命令删除）----"
sed -e "/^#/d" -e "/^$/d" "$WORK_DIR/app.conf"

# === 4. sed 打印命令 p（配合 -n）===
echo ""
echo ">>> [4] sed 打印命令 p（配合 -n 安静模式）..."

echo "---- sed -n '1p' sample.txt（仅打印第 1 行）----"
sed -n "1p" "$WORK_DIR/sample.txt"

echo ""
echo "---- sed -n '2,4p' sample.txt（打印第 2-4 行）----"
sed -n "2,4p" "$WORK_DIR/sample.txt"

echo ""
echo "---- sed -n '\$p' sample.txt（打印最后一行）----"
sed -n '$p' "$WORK_DIR/sample.txt"

echo ""
echo "---- sed -n '/Linux/p' sample.txt（打印含 Linux 的行，等同 grep）----"
sed -n "/Linux/p" "$WORK_DIR/sample.txt"

echo ""
echo "---- sed -n '1~2p' sample.txt（打印奇数行，步长 2）----"
sed -n "1~2p" "$WORK_DIR/sample.txt"

echo ""
echo "---- sed -n '2~2p' sample.txt（打印偶数行）----"
sed -n "2~2p" "$WORK_DIR/sample.txt"

# === 5. sed 追加 a / 插入 i / 修改 c ===
echo ""
echo ">>> [5] sed 追加 a / 插入 i / 修改 c..."

echo "---- sed '2a\NEW LINE' sample.txt（第 2 行后追加）----"
sed "2a\\NEW LINE" "$WORK_DIR/sample.txt"

echo ""
echo "---- sed '2i\INSERTED LINE' sample.txt（第 2 行前插入）----"
sed "2i\\INSERTED LINE" "$WORK_DIR/sample.txt"

echo ""
echo "---- sed '/api/a\\    # API 反向代理配置已添加' nginx.conf（匹配行后追加）----"
sed "/location \/api\//a\\    # API 反向代理配置已添加" "$WORK_DIR/nginx.conf" | grep -A 1 "api"

echo ""
echo "---- sed '3c\REPLACED LINE' sample.txt（第 3 行整行替换）----"
sed "3c\\REPLACED LINE" "$WORK_DIR/sample.txt"

echo ""
echo "---- sed '/Hello/c\\GREETING' sample.txt（含 Hello 的行替换为 GREETING）----"
sed "/Hello/c\\GREETING" "$WORK_DIR/sample.txt"

# === 6. sed -e 多命令组合 ===
echo ""
echo ">>> [6] sed -e 多命令组合..."

echo "---- sed -e 's/Hello/Hi/g' -e 's/World/Earth/g' sample.txt（多个替换）----"
sed -e "s/Hello/Hi/g" -e "s/World/Earth/g" "$WORK_DIR/sample.txt"

echo ""
echo "---- sed -e '/^#/d' -e '/^$/d' -e 's/OldPassword123/NewSecurePass456/' app.conf（删除注释空行+替换密码）----"
sed -e "/^#/d" -e "/^$/d" -e "s/OldPassword123/NewSecurePass456/" "$WORK_DIR/app.conf"

echo ""
echo "---- sed 's/Hello/Hi/g; s/World/Earth/g' sample.txt（分号分隔多命令）----"
sed "s/Hello/Hi/g; s/World/Earth/g" "$WORK_DIR/sample.txt"

# === 7. sed -n 高级用法 ===
echo ""
echo ">>> [7] sed -n 高级用法..."

echo "---- sed -n '1,3=' sample.txt（打印第 1-3 行的行号）----"
sed -n "1,3=" "$WORK_DIR/sample.txt"

echo ""
echo "---- sed -n '/Hello/{=;p}' sample.txt（含 Hello 的行：先打印行号再打印内容）----"
sed -n "/Hello/{=;p}" "$WORK_DIR/sample.txt"

echo ""
echo "---- sed -n '1p;3p;5p' sample.txt（打印第 1、3、5 行）----"
sed -n "1p;3p;5p" "$WORK_DIR/sample.txt"

# === 8. sed -i 原地修改文件 ===
echo ""
echo ">>> [8] sed -i 原地修改文件..."

# 先复制一份用于修改
cp "$WORK_DIR/app.conf" "$WORK_DIR/app-modified.conf"

echo "---- sed -i 's/OldPassword123/NewSecurePass456/' app-modified.conf（原地修改）----"
sed -i "s/OldPassword123/NewSecurePass456/" "$WORK_DIR/app-modified.conf"
echo "    修改后含 password 的行："
grep "password" "$WORK_DIR/app-modified.conf"

echo ""
echo "---- sed -i.bak 's/OldRedisPass/NewRedisPass789/' app-modified.conf（修改并备份）----"
sed -i.bak "s/OldRedisPass/NewRedisPass789/" "$WORK_DIR/app-modified.conf"
echo "    修改后含 redis_password 的行："
grep "redis_password" "$WORK_DIR/app-modified.conf"
echo "    备份文件："
ls -la "$WORK_DIR/app-modified.conf.bak"

echo ""
echo "---- sed -i -e '/^#/d' -e '/^$/d' app-modified.conf（原地删除注释和空行）----"
sed -i -e "/^#/d" -e "/^$/d" "$WORK_DIR/app-modified.conf"
echo "    修改后内容："
cat "$WORK_DIR/app-modified.conf"

# === 9. sed 批量修改配置文件实战 ===
echo ""
echo ">>> [9] sed 批量修改配置文件实战..."

# 复制 nginx 配置用于修改
cp "$WORK_DIR/nginx.conf" "$WORK_DIR/nginx-modified.conf"

echo "---- 批量修改 Nginx 配置 ----"
echo "    原始配置关键行："
grep -E "listen|server_name|root|proxy_pass" "$WORK_DIR/nginx-modified.conf"

echo ""
echo "    执行批量修改："
sed -i \
    -e "s/listen 80;/listen 8080;/" \
    -e "s/example.com/myshop.com/g" \
    -e "s/www.myshop.com/www.myshop.com/" \
    -e "s|/var/www/ecommerce|/opt/ecommerce/frontend|g" \
    -e "s|http://localhost:3000|http://127.0.0.1:3000|" \
    -e "s|# 电商项目服务|# 电商项目服务（已修改）|" \
    "$WORK_DIR/nginx-modified.conf"

echo "    修改后关键行："
grep -E "listen|server_name|root|proxy_pass|# 电商" "$WORK_DIR/nginx-modified.conf"

# === 10. sed 删除 Windows 换行符 ===
echo ""
echo ">>> [10] sed 删除 Windows 换行符..."

echo "---- 原始 windows-file.txt（含 \\r，用 cat -A 可见）----"
cat -A "$WORK_DIR/windows-file.txt"

echo ""
echo "---- sed 's/\r$//' windows-file.txt（删除行尾 \\r）----"
sed "s/\r$//" "$WORK_DIR/windows-file.txt" | cat -A

echo ""
echo "---- sed -i 's/\r$//' windows-file.txt（原地修改）----"
sed -i "s/\r$//" "$WORK_DIR/windows-file.txt"
echo "    修改后："
cat -A "$WORK_DIR/windows-file.txt"

# === 11. sed 文本格式化 ===
echo ""
echo ">>> [11] sed 文本格式化..."

echo "---- sed 's/^/    /' sample.txt（行首加 4 空格缩进）----"
sed "s/^/    /" "$WORK_DIR/sample.txt" | head -n 3

echo ""
echo "---- sed 's/$/;/' sample.txt（行尾加分号）----"
sed "s/\$\/;/" "$WORK_DIR/sample.txt" 2>/dev/null || sed 's/$/;/' "$WORK_DIR/sample.txt"
echo "    （行尾加分号）"

echo ""
echo "---- sed 's/  */ /g' app.conf（多个空格压缩为一个）----"
sed "s/  */ /g" "$WORK_DIR/app.conf" | head -n 5

echo ""
echo "---- sed 's/^[ \t]*//' sample.txt（删除行首空格/Tab）----"
sed "s/^[ \t]*//" "$WORK_DIR/sample.txt" | head -n 3

echo ""
echo "---- sed G sample.txt（每行后加空行，G 是 GNU 扩展）----"
sed G "$WORK_DIR/sample.txt" | head -n 4

# === 12. sed 综合实战 ===
echo ""
echo ">>> [12] sed 综合实战..."

echo "---- 场景 1：提取 Nginx 配置中所有 location 块 ----"
sed -n "/location/p" "$WORK_DIR/nginx.conf"

echo ""
echo "---- 场景 2：把 app.conf 的 debug=true 改为 debug=false ----"
sed "s/debug=true/debug=false/" "$WORK_DIR/app.conf" | grep "debug"

echo ""
echo "---- 场景 3：给所有非注释非空行加行号 ----"
sed -n "/^[^#]/=" "$WORK_DIR/app.conf" | head -n 5

echo ""
echo "---- 场景 4：提取端口号 ----"
sed -n "s/.*port=\([0-9]*\).*/\1/p" "$WORK_DIR/app.conf"

echo ""
echo "---- 场景 5：统计 nginx.conf 中除注释和空行外的有效配置行数 ----"
sed -e "/^#/d" -e "/^$/d" -e "/^ *#/d" "$WORK_DIR/nginx.conf" | wc -l
echo "    （以上为 nginx.conf 有效配置行数）"

echo ""
echo "================================================"
echo "  sed 演示完成！"
echo "  素材保留在：$WORK_DIR"
echo "  清理：rm -rf $WORK_DIR"
echo "================================================"
