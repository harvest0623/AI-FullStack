-- ============================================================
-- 文件：03-lua-inventory.lua
-- 用途：原子库存扣减 Lua 脚本
-- 场景：电商下单扣减库存，需"检查库存 → 扣减 → 返回结果"原子完成
-- 执行：redis-cli --eval 03-lua-inventory.lua stock:product:1001 , 1
--       （逗号前是 KEYS，逗号后是 ARGV）
--
-- 参数说明：
--   KEYS[1] = 库存 key，例如 stock:product:1001
--   ARGV[1] = 扣减数量（正整数）
--
-- 返回值：
--    1  → 扣减成功
--    0  → 库存不足
--   -1  → key 不存在或不是数字
--   -2  → 参数非法（扣减数 <= 0）
-- ============================================================

local stock_key = KEYS[1]
local need = tonumber(ARGV[1])

-- 参数校验
if need == nil or need <= 0 then
    return -2
end

-- 读取当前库存
local stock_str = redis.call('GET', stock_key)
if stock_str == false or stock_str == nil then
    return -1
end

local stock = tonumber(stock_str)
if stock == nil then
    return -1
end

-- 判断库存是否充足
if stock >= need then
    redis.call('DECRBY', stock_key, need)
    return 1
else
    return 0
end
