// Day10 - server_actions.js  Server Action 流程演示
// 模拟：表单提交 → 服务端函数 → 解析 formData → 校验 → revalidate 刷新。
// 离线可运行：node server_actions.js

// 模拟数据库
let todos = ['学习 Next.js', '学习路由'];

function revalidatePath(path) {
  return `[revalidatePath('${path}')] 标记该路径缓存失效，下次请求刷新数据`;
}

// 模拟 Server Action：createTodo
async function createTodo(formData) {
  const text = formData['text'] || '';
  console.log('  服务端执行 createTodo(formData)...');

  // 校验
  if (text.trim().length < 2) {
    console.log('  → 校验失败：名称至少 2 个字符（可通过 useActionState 回显错误）');
    return { error: '名称至少 2 个字符' };
  }

  todos = [...todos, text.trim()];
  console.log('  → 写入成功');
  console.log('  → ' + revalidatePath('/todos'));
  return { error: null };
}

// 模拟 Server Action：deleteTodo（用 bind 绑定 id）
async function deleteTodo(id) {
  console.log(`  服务端执行 deleteTodo(id=${id})（id 由 bind 预绑定）...`);
  todos = todos.filter((_, i) => i !== id - 1);
  console.log('  → ' + revalidatePath('/todos'));
}

function main() {
  console.log('【Server Actions 流程演示】\n');

  console.log('① 表单提交新增（无 JS 也行的渐进增强）\n');
  console.log('  初始 todos：', todos);
  createTodo({ text: '学习 Server Actions' });

  console.log('\n  再次提交非法数据：');
  createTodo({ text: 'a' });

  console.log('\n  当前 todos：', todos);

  console.log('\n② 用 bind 绑定额外参数删除\n');
  deleteTodo(1);

  console.log('\n  最终 todos：', todos);

  console.log('\n【要点】');
  console.log('  · action 在服务端执行，可访问数据库与私密变量');
  console.log('  · 无 JS 时表单用原生 action 也能提交（渐进增强）');
  console.log('  · revalidatePath 让新数据在下一次请求生效');
  console.log('  · useActionState 回显校验错误；useOptimistic 做乐观更新');
}

main();