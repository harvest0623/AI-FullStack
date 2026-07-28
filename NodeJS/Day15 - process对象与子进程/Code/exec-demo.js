// exec-demo.js - 对比 exec / execFile，演示命令注入风险与安全写法
// 运行:
//   node exec-demo.js

const { exec, execFile } = require('child_process');

// ---------------------------------------------------------------
// 1. exec：缓冲执行，回调里一次性拿到 stdout/stderr
// ---------------------------------------------------------------
function demoExec() {
  console.log('=== 1. exec 缓冲执行 ===');
  exec('node --version', (err, stdout, stderr) => {
    if (err) {
      console.error('exec 失败:', err);
      return;
    }
    console.log('node 版本(exec):', stdout.trim());
    if (stderr) console.log('stderr:', stderr.trim());
  });
}

// ---------------------------------------------------------------
// 2. exec 的 maxBuffer 限制：超过会被 kill
// ---------------------------------------------------------------
function demoMaxBuffer() {
  console.log('\n=== 2. maxBuffer 限制 ===');
  // 默认 maxBuffer = 1MB。这里让 node 输出 2MB，会触发 maxBuffer 错误
  exec('node -e "process.stdout.write(Buffer.alloc(2*1024*1024))"',
    { maxBuffer: 1024 * 1024 }, // 1MB
    (err, stdout, stderr) => {
      if (err) {
        console.log('如预期触发 maxBuffer 错误:', err.message.split('\n')[0]);
        console.log('→ 大输出场景应改用 spawn 流式读取');
      } else {
        console.log('输出长度:', stdout.length);
      }
    }
  );
}

// ---------------------------------------------------------------
// 3. ❌ 危险示例：exec 拼接用户输入导致命令注入
//    本例用恶意字符串模拟"用户提交的文件名"，展示后果
//    注释掉的代码是危险写法，仅作教学说明，不在本机真实执行 rm
// ---------------------------------------------------------------
function demoInjectionRisk() {
  console.log('\n=== 3. 命令注入风险（仅说明，不真实执行）===');

  // 假设这是从前端/接口收到的"文件名"
  const maliciousFileName = 'foo.txt; echo INJECTED';

  // ❌ 危险写法：把用户输入直接拼到 shell 命令字符串
  // exec(`wc -c ${maliciousFileName}`, ...) 实际会执行：
  //   wc -c foo.txt; echo INJECTED
  // 即先 wc foo.txt，再执行 echo INJECTED。
  // 如果换成 '; rm -rf /'，后果不堪设想。
  // 更隐蔽的注入: $(cmd)、`cmd`、> 重定向、&& / || 串联

  // 这里我们用"无害"的 echo 来演示——但本质是一样的
  exec(`echo ${maliciousFileName}`, (err, stdout) => {
    if (err) return console.error(err);
    console.log('危险写法实际输出:', stdout.trim());
    console.log('→ 后半段 "echo INJECTED" 被当作独立命令执行了！');
  });
}

// ---------------------------------------------------------------
// 4. ✅ 安全写法：用 execFile + 参数数组，不启动 shell
//    参数作为 argv 单独传递，OS 层面不会被 shell 重新解析
// ---------------------------------------------------------------
function demoSafe() {
  console.log('\n=== 4. execFile 安全写法 ===');
  const userInput = 'foo.txt; echo INJECTED';

  // 即使 userInput 含 shell 元字符，也只被当作单个参数
  // 等价于: echo "foo.txt; echo INJECTED"（整体作为 echo 的第一个参数）
  execFile('echo', [userInput], (err, stdout, stderr) => {
    if (err) return console.error(err);
    console.log('execFile 输出:', stdout.trim());
    console.log('→ 注入字符串被原样输出，未被解释为命令');
  });
}

// ---------------------------------------------------------------
// 5. exec vs execFile 性能与语义对比
// ---------------------------------------------------------------
function demoCompare() {
  console.log('\n=== 5. exec vs execFile 对比 ===');

  // exec 走 shell，支持管道符、通配符等 shell 语法
  exec('node -e "console.log(1+1)" | findstr 2', (err, stdout) => {
    // Windows: 用 findstr；Linux: 可改成 grep
    if (err) {
      console.log('exec(管道) 在当前平台可能不工作:', err.message.split('\n')[0]);
    } else {
      console.log('exec 管道结果:', stdout.trim());
    }
  });

  // execFile 不走 shell，不支持管道符——但更快、更安全
  execFile(process.execPath, ['-e', 'console.log(2+2)'], (err, stdout) => {
    if (err) return console.error(err);
    console.log('execFile 结果:', stdout.trim(), '(无 shell 开销)');
  });
}

// 依次执行（保持输出顺序）
setTimeout(() => {
  demoExec();
  setTimeout(demoMaxBuffer, 100);
  setTimeout(demoInjectionRisk, 200);
  setTimeout(demoSafe, 300);
  setTimeout(demoCompare, 400);
}, 50);

// ---------------------------------------------------------------
// 总结注释
// ---------------------------------------------------------------
/*
  安全规则速记：
  1. 用户输入参与命令时，永远用 execFile / spawn + 参数数组
  2. 避免 exec 与 spawn({ shell: true }) 拼接用户输入
  3. 文件名参数可用 path.resolve 锁定目录、拒绝 '..'
  4. 密钥/敏感参数走 env，不要拼到命令行（命令行在 ps 中可见）
  5. exec 适合：输出小、需要 shell 语法的场景（管道、通配）
  6. execFile 适合：输出小、用户输入参与、追求安全的场景
  7. spawn 适合：输出大或需要流式处理的场景
  8. fork 适合：Node 子进程 + IPC 通信
*/
