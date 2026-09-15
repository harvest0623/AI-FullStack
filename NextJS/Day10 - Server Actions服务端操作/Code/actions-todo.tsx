// Day10 - actions.ts + todo-page.tsx  Server Action + 表单示例
// actions.ts 落位：app/actions.ts；todo-page.tsx 落位：app/todos/page.tsx

// ============ app/actions.ts ============
'use server';

import { revalidatePath } from 'next/cache';

let todos: { id: number; text: string }[] = [
  { id: 1, text: '学习 Next.js' },
];

// 新增（表单直接用）
export async function createTodo(formData: FormData) {
  const text = formData.get('text')?.toString() ?? '';
  if (text.trim().length < 2) {
    return { error: '名称至少 2 个字符' };
  }
  todos = [...todos, { id: Date.now(), text: text.trim() }];
  revalidatePath('/todos'); // 刷新列表，无需手动获取
  return { error: null };
}

// 删除（通过 bind 绑定 id）
export async function deleteTodo(id: number) {
  todos = todos.filter((t) => t.id !== id);
  revalidatePath('/todos');
}

// ============ app/todos/page.tsx ============
import Link from 'next/link';
import { createTodo, deleteTodo } from '@/app/actions';

export default function TodosPage() {
  return (
    <main style={{ padding: 40, maxWidth: 520, margin: '0 auto' }}>
      <h2>Todo（Server Actions）</h2>

      {/* 表单提交：把字段收集为 FormData 传给 createTodo */}
      <form action={createTodo} style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input name="text" placeholder="新事项，至少 2 个字符" style={{ flex: 1, padding: 8 }} />
        <button type="submit">创建</button>
      </form>

      <ul style={{ listStyle: 'none', padding: 0 }}>
        {todos.map((t) => (
          <li key={t.id} style={{ display: 'flex', justifyContent: 'space-between', padding: 8, borderBottom: '1px solid #eee' }}>
            <span>{t.text}</span>
            {/* 用 bind 预绑定 id，删除对应 todo */}
            <form action={deleteTodo.bind(null, t.id)}>
              <button type="submit">删除</button>
            </form>
          </li>
        ))}
      </ul>

      <Link href="/">返回首页</Link>
    </main>
  );
}