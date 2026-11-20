#!/bin/bash
# ============================================================
# 文件名：03-curl-wget.sh
# 用途：演示 curl/wget 命令，覆盖 GET/POST/PUT/DELETE、各种选项、
#       文件下载、API 测试实战
# 适用：Ubuntu 22.04 LTS
# 场景：电商项目 API 接口测试（httpbin.org 提供在线测试接口）
# ============================================================

cd "$(dirname "$0")" || exit 1

echo "============================================================"
echo "  Day06 - 03 curl/wget 命令演示"
echo "  电商 API 测试实战（使用 httpbin.org 在线测试服务）"
echo "============================================================"

# 测试目标（httpbin.org 是免费的 HTTP 测试服务）
API_BASE="https://httpbin.org"
LOCAL_API="http://127.0.0.1:3000/api"

# ---------- 1. curl 基础 GET ----------

echo -e "\n[1] curl 基础 GET 请求"
echo "命令：curl $API_BASE/get"
curl -s "$API_BASE/get" | head -n 20
echo ""
echo "说明：-s 静默模式（不显示进度条），输出为 JSON"

echo -e "\n[2] curl -i —— 显示响应头和正文"
echo "命令：curl -i -s $API_BASE/get | head -n 15"
curl -i -s "$API_BASE/get" | head -n 15

echo -e "\n[3] curl -I —— 仅查看响应头"
echo "命令：curl -I -s $API_BASE/get"
curl -I -s "$API_BASE/get"

echo -e "\n[4] curl -v —— 详细过程（调试用）"
echo "命令：curl -v -o /dev/null -s $API_BASE/get 2>&1 | head -n 20"
curl -v -o /dev/null -s "$API_BASE/get" 2>&1 | head -n 20
echo "说明：> 表示请求行/请求头；< 表示响应行/响应头；* 表示 curl 提示信息"

echo -e "\n[5] curl -w —— 输出 HTTP 状态码"
echo "命令：curl -s -o /dev/null -w '%{http_code}\n' $API_BASE/get"
curl -s -o /dev/null -w "%{http_code}\n" "$API_BASE/get"

echo -e "\n[6] curl -w —— 详细计时信息（性能排查）"
echo "命令：curl -o /dev/null -s -w 'DNS:%{time_namelookup} Connect:%{time_connect} TTFB:%{time_starttransfer} Total:%{time_total}\n' $API_BASE/get"
curl -o /dev/null -s -w "DNS:%{time_namelookup} Connect:%{time_connect} TTFB:%{time_starttransfer} Total:%{time_total}\n" "$API_BASE/get"
echo "说明：DNS=DNS解析耗时 Connect=TCP连接耗时 TTFB=首字节时间 Total=总耗时"

# ---------- 2. curl 超时设置 ----------

echo -e "\n[7] curl —— 超时设置"
echo "命令：curl --connect-timeout 5 --max-time 10 -s $API_BASE/get"
curl --connect-timeout 5 --max-time 10 -s "$API_BASE/get" -o /dev/null -w "状态码：%{http_code}\n"
echo "说明：--connect-timeout 连接超时；--max-time 总超时（含传输）"

# ---------- 3. curl GET 带查询参数 ----------

echo -e "\n[8] curl GET 带查询参数"
echo "命令：curl -s '$API_BASE/get?userId=1&name=alice'"
curl -s "$API_BASE/get?userId=1&name=alice" | head -n 20

# ---------- 4. curl POST 请求 ----------

echo -e "\n[9] curl POST —— 表单提交（application/x-www-form-urlencoded）"
echo "命令：curl -s -X POST -d 'name=alice&email=alice@example.com' $API_BASE/post"
curl -s -X POST -d "name=alice&email=alice@example.com" "$API_BASE/post" | head -n 25

echo -e "\n[10] curl POST —— JSON 提交（最常用）"
echo "命令：curl -s -X POST -H 'Content-Type: application/json' -d '{\"name\":\"alice\",\"age\":25}' $API_BASE/post"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"name":"alice","age":25,"hobbies":["reading","coding"]}' \
  "$API_BASE/post" | head -n 30

echo -e "\n[11] curl POST —— 从文件读取 JSON body"
# 准备测试 JSON 文件
cat > /tmp/test-payload.json <<'EOF'
{
  "userId": 1,
  "items": [
    {"productId": 101, "quantity": 2},
    {"productId": 205, "quantity": 1}
  ],
  "address": "北京市朝阳区"
}
EOF
echo "命令：curl -s -X POST -H 'Content-Type: application/json' -d @/tmp/test-payload.json $API_BASE/post"
curl -s -X POST -H "Content-Type: application/json" \
  -d @/tmp/test-payload.json "$API_BASE/post" | head -n 30

# ---------- 5. curl PUT / DELETE ----------

echo -e "\n[12] curl PUT —— 更新资源"
echo "命令：curl -s -X PUT -H 'Content-Type: application/json' -d '{\"name\":\"bob\"}' $API_BASE/put"
curl -s -X PUT -H "Content-Type: application/json" \
  -d '{"name":"bob","age":30}' "$API_BASE/put" | head -n 25

echo -e "\n[13] curl DELETE —— 删除资源"
echo "命令：curl -s -X DELETE $API_BASE/delete"
curl -s -X DELETE "$API_BASE/delete" | head -n 20

# ---------- 6. curl 自定义请求头 ----------

echo -e "\n[14] curl —— 携带 Authorization Token"
echo "命令：curl -s -H 'Authorization: Bearer eyJhbGc...' $API_BASE/headers"
curl -s -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.signature" \
  "$API_BASE/headers" | head -n 20

echo -e "\n[15] curl —— 携带多个请求头"
echo "命令：curl -s -H 'X-Request-ID: abc123' -H 'X-Client: web' $API_BASE/headers"
curl -s -H "X-Request-ID: abc123" -H "X-Client: web" -H "Accept-Language: zh-CN" \
  "$API_BASE/headers" | head -n 25

# ---------- 7. curl Cookie 处理 ----------

echo -e "\n[16] curl —— 携带 Cookie"
echo "命令：curl -s --cookie 'session=abc123; user=alice' $API_BASE/cookies"
curl -s --cookie "session=abc123; user=alice" "$API_BASE/cookies"

echo -e "\n[17] curl —— 保存与加载 Cookie"
echo "命令：curl -s -c /tmp/cookies.txt -X POST -d 'user=admin&pass=secret' $API_BASE/cookies/set"
curl -s -c /tmp/cookies.txt -X POST -d "user=admin" "$API_BASE/cookies/set?user=admin" -o /dev/null
echo "保存的 Cookie 文件内容："
cat /tmp/cookies.txt | tail -n 5
echo ""
echo "命令：curl -s -b /tmp/cookies.txt $API_BASE/cookies"
curl -s -b /tmp/cookies.txt "$API_BASE/cookies"

# ---------- 8. curl 重定向 ----------

echo -e "\n[18] curl -L —— 跟随重定向"
echo "命令：curl -s -L -o /dev/null -w '%{http_code} %{url_effective}\n' $API_BASE/redirect/2"
curl -s -L -o /dev/null -w "最终状态码：%{http_code}\n最终URL：%{url_effective}\n" \
  "$API_BASE/redirect/2"
echo "说明：不加 -L 则返回 302 状态码，不跟随跳转"

# ---------- 9. curl 自定义 DNS 解析 ----------

echo -e "\n[19] curl --resolve —— 自定义 DNS 解析（绕过 DNS）"
echo "命令：curl -s --resolve httpbin.org:443:54.92.219.0X $API_BASE/get"
echo "说明：可强制将 httpbin.org 解析到指定 IP，用于测试负载均衡、灰度发布"
echo "      电商场景：让 api.example.com 临时指向测试服务器 IP"
cat <<'EOF'
curl --resolve api.example.com:443:192.168.1.100 https://api.example.com/health
EOF

# ---------- 10. curl 文件下载 ----------

echo -e "\n[20] curl -o —— 下载到指定文件"
echo "命令：curl -s -o /tmp/curl-test.json -w '%{http_code} %{size_download} bytes\n' $API_BASE/json"
curl -s -o /tmp/curl-test.json -w "状态码：%{http_code} 大小：%{size_download} bytes\n" "$API_BASE/json"
echo "下载文件内容预览："
head -n 5 /tmp/curl-test.json

echo -e "\n[21] curl -O —— 用原文件名下载"
echo "命令：curl -s -O https://raw.githubusercontent.com/torvalds/linux/master/COPYING"
cd /tmp
curl -s -O "https://raw.githubusercontent.com/torvalds/linux/master/COPYING" 2>/dev/null && echo "下载成功：$(ls -lh COPYING | awk '{print $9, $5}')" || echo "（下载失败，可能网络问题）"
ls -lh COPYING 2>/dev/null
rm -f COPYING
cd - >/dev/null

# ---------- 11. curl 文件上传 ----------

echo -e "\n[22] curl -F —— 文件上传（multipart/form-data）"
# 准备测试文件
echo "Hello, this is a test file for upload." > /tmp/upload-test.txt
echo "命令：curl -s -F 'file=@/tmp/upload-test.txt' -F 'userId=1' $API_BASE/post"
curl -s -F "file=@/tmp/upload-test.txt" -F "userId=1" "$API_BASE/post" | head -n 25

# ---------- 12. wget 文件下载 ----------

echo -e "\n[23] wget —— 基础下载"
if command -v wget >/dev/null 2>&1; then
    echo "命令：wget -q -O /tmp/wget-test.json $API_BASE/json"
    wget -q -O /tmp/wget-test.json "$API_BASE/json"
    echo "下载内容预览："
    head -n 5 /tmp/wget-test.json
else
    echo "未安装 wget，可执行：sudo apt install -y wget"
fi

echo -e "\n[24] wget —— 断点续传（-c）"
cat <<'EOF'
wget -c http://example.com/large-file.iso
说明：如果下载中断，再次执行会从断点继续，而不是从头开始

wget -c --limit-rate=1M http://example.com/large-file.iso  # 限速 1MB/s
EOF

echo -e "\n[25] wget —— 递归下载（镜像网站）"
cat <<'EOF'
wget -r -l 2 -np http://example.com/docs/
# -r 递归 / -l 2 递归深度 / -np 不追溯到父目录

wget -r -l 1 -A pdf http://example.com/docs/  # 只下载 PDF 文件
# -A 指定接受的文件类型
EOF

echo -e "\n[26] wget —— 后台下载大文件"
cat <<'EOF'
wget -b http://example.com/large-file.iso
# 输出会写入 wget-log，可用 tail -f wget-log 跟踪进度
EOF

# ---------- 13. 电商 API 测试实战示例 ----------

echo -e "\n[27] 电商 API 测试实战示例（打印命令模板）"
cat <<'EOF'
# 假设电商后端部署在 192.168.1.100:3000
API=http://192.168.1.100:3000/api

# 1. 健康检查
curl -s -w "\n状态码：%{http_code}\n" $API/health

# 2. 用户登录并保存 Cookie
curl -s -c /tmp/ecommerce-cookies.txt -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"secret"}' \
  $API/auth/login

# 3. 携带 Cookie 查询商品列表
curl -s -b /tmp/ecommerce-cookies.txt $API/products?page=1&size=20

# 4. 提交订单（JSON body）
curl -s -b /tmp/ecommerce-cookies.txt -X POST \
  -H "Content-Type: application/json" \
  -d '{"items":[{"productId":101,"quantity":2}],"addressId":1}' \
  $API/orders

# 5. 性能压测单接口
for i in {1..100}; do
  curl -s -o /dev/null -w "%{http_code} %{time_total}\n" $API/products/1
done | awk '{sum+=$2; count++} END {print "平均响应时间:", sum/count, "秒"}'

# 6. 携带 Token（JWT 认证）
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
curl -s -H "Authorization: Bearer $TOKEN" $API/profile
EOF

# 清理临时文件
rm -f /tmp/test-payload.json /tmp/cookies.txt /tmp/curl-test.json /tmp/wget-test.json /tmp/upload-test.txt 2>/dev/null

echo -e "\n============================================================"
echo "  Day06 - 03 curl/wget 命令演示 完成"
echo "============================================================"
