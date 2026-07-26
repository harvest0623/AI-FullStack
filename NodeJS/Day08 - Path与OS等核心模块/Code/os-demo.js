// Day08 - os 模块演示
// 主题：平台/CPU 核数/内存/网络接口/负载 + 按 CPU 核数计算并发数
// 运行：node Code/os-demo.js
//
// 说明：os 模块全部为同步、廉价的只读接口，可放心在启动时调用；
// 注意容器环境下 os.cpus() 可能返回宿主机核数，与 cgroup 限制不一致。

const os = require('os');

console.log('========================================');
console.log(' Day08 - os 模块演示');
console.log('========================================\n');

// ---------------------------------------------------------------
// 1. 系统基本信息
// ---------------------------------------------------------------
console.log('--- 1. 系统基本信息 ---');
console.log(`  platform   : ${os.platform()}`);
console.log(`  arch       : ${os.arch()}`);
console.log(`  type       : ${os.type()}`);
console.log(`  release    : ${os.release()}`);
console.log(`  hostname   : ${os.hostname()}`);
console.log(`  endianness : ${os.endianness()}`);
console.log(`  homedir    : ${os.homedir()}`);
console.log(`  tmpdir     : ${os.tmpdir()}`);
console.log(`  uptime     : ${(os.uptime() / 3600).toFixed(2)} 小时`);

// ---------------------------------------------------------------
// 2. CPU 信息
// ---------------------------------------------------------------
console.log('\n--- 2. CPU 信息 ---');
const cpus = os.cpus();
console.log(`  逻辑核心数 : ${cpus.length}`);
if (cpus.length > 0) {
  console.log(`  型号       : ${cpus[0].model}`);
  console.log(`  主频       : ${cpus[0].speed} MHz`);
  console.log('  核 0 时间片（ms）：');
  const t = cpus[0].times;
  console.log(`     user=${t.user}  nice=${t.nice}  sys=${t.sys}  idle=${t.idle}  irq=${t.irq}`);
}

// ---------------------------------------------------------------
// 3. 负载（loadavg）
// ---------------------------------------------------------------
console.log('\n--- 3. 系统负载 loadavg（1/5/15 分钟平均）---');
const load = os.loadavg();
console.log(`  1 分钟  : ${load[0].toFixed(2)}`);
console.log(`  5 分钟  : ${load[1].toFixed(2)}`);
console.log(`  15 分钟 : ${load[2].toFixed(2)}`);
console.log(`  ⚠️ Windows 上 loadavg 永远返回 [0,0,0]`);
if (os.platform() !== 'win32') {
  const ratio = load[0] / cpus.length;
  console.log(`  load/cpu = ${ratio.toFixed(2)}（>0.7 需警惕 CPU 瓶颈）`);
}

// ---------------------------------------------------------------
// 4. 内存信息
// ---------------------------------------------------------------
console.log('\n--- 4. 内存信息 ---');
const GB = 1024 ** 3;
const total = os.totalmem();
const free = os.freemem();
console.log(`  总内存   : ${(total / GB).toFixed(2)} GB`);
console.log(`  可用内存 : ${(free / GB).toFixed(2)} GB`);
console.log(`  已用比例 : ${((1 - free / total) * 100).toFixed(1)}%`);

// 进程视角：process.memoryUsage（不在 os 模块，但常一起看）
const mu = process.memoryUsage();
console.log('  当前 Node 进程：');
console.log(`     rss            : ${(mu.rss / GB).toFixed(3)} GB  ← 常驻集`);
console.log(`     heapUsed       : ${(mu.heapUsed / 1024 ** 2).toFixed(2)} MB  ← 已用堆`);
console.log(`     heapTotal      : ${(mu.heapTotal / 1024 ** 2).toFixed(2)} MB  ← 已分配堆`);
console.log(`     external       : ${(mu.external / 1024 ** 2).toFixed(2)} MB  ← C++ 对象`);

// ---------------------------------------------------------------
// 5. 网络接口
// ---------------------------------------------------------------
console.log('\n--- 5. 网络接口 ---');
const nets = os.networkInterfaces();
const localIPs = [];
for (const [name, addrs] of Object.entries(nets)) {
  for (const a of addrs) {
    if (a.family === 'IPv4' && !a.internal) {
      localIPs.push({ name, address: a.address });
    }
  }
}
console.log(`  非环回 IPv4 地址（共 ${localIPs.length} 个）：`);
localIPs.forEach((x, i) => console.log(`    [${i}] ${x.name}: ${x.address}`));
if (localIPs.length > 0) {
  console.log(`  → 选第一个作为本机 IP：${localIPs[0].address}`);
}

// ---------------------------------------------------------------
// 6. EOL 换行符
// ---------------------------------------------------------------
console.log('\n--- 6. EOL 换行符 ---');
console.log(`  os.EOL = ${JSON.stringify(os.EOL)}`);
console.log(`  POSIX 为 \\n，Windows 为 \\r\\n`);

// ---------------------------------------------------------------
// 7. userInfo 与 constants
// ---------------------------------------------------------------
console.log('\n--- 7. 用户信息与信号常量 ---');
const u = os.userInfo();
console.log(`  username : ${u.username}`);
console.log(`  homedir  : ${u.homedir}`);
console.log(`  shell    : ${u.shell || '(Windows 无此字段)'}`);
console.log(`  uid/gid  : ${u.uid}/${u.gid}（Windows 上为 -1）`);

console.log('  常用信号编号：');
console.log(`    SIGTERM = ${os.constants.signals.SIGTERM}`);
console.log(`    SIGINT  = ${os.constants.signals.SIGINT}`);
console.log(`    SIGHUP  = ${os.constants.signals.SIGHUP}`);

// ---------------------------------------------------------------
// 8. 实战：按 CPU 核数计算推荐并发数
// ---------------------------------------------------------------
console.log('\n--- 8. 实战：自适应并发数计算 ---');

function concurrencyHint() {
  const cpuCount = cpus.length;
  const freeGB = free / GB;
  const load1 = load[0];

  // 默认留 1 核给主进程
  let hint = Math.max(1, cpuCount - 1);

  // 内存告急：可用内存不足 1GB 时砍半
  let reason = `默认 cpu-1 = ${hint}`;
  if (freeGB < 1) {
    hint = Math.max(1, Math.floor(hint / 2));
    reason += ` → 内存不足 1GB（${freeGB.toFixed(2)}GB），砍半 → ${hint}`;
  }

  // 系统高负载（仅 POSIX 有意义）
  if (os.platform() !== 'win32' && load1 > cpuCount * 0.8) {
    hint = 1;
    reason += ` → load1(${load1.toFixed(2)}) > cpu*0.8(${(cpuCount * 0.8).toFixed(2)})，砍到 1 → ${hint}`;
  }

  return { hint, cpuCount, freeGB, load1, reason };
}

const r = concurrencyHint();
console.log(`  CPU 核数  : ${r.cpuCount}`);
console.log(`  可用内存  : ${r.freeGB.toFixed(2)} GB`);
console.log(`  load(1m) : ${r.load1.toFixed(2)}`);
console.log(`  推荐并发 : ${r.hint}`);
console.log(`  决策过程 : ${r.reason}`);

// ---------------------------------------------------------------
console.log('\n=== 要点回顾 ===');
console.log('  1. os.cpus().length 给并发池大小的初始依据；');
console.log('  2. os.freemem()/totalmem() 用于判断能否加载大模型；');
console.log('  3. 容器内 os.cpus() 可能返回宿主机核数，需读 cgroup 才能拿到真实限制；');
console.log('  4. os.networkInterfaces() 是拿本机 IP 的标准方式；');
console.log('  5. os.loadavg 在 Windows 上恒为 [0,0,0]，做负载判断要排除 Windows。');
