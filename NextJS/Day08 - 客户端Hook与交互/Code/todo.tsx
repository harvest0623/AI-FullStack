// Day08 - todo.tsx  受控表单 + 状态管理 + 交互示例
// 落位：app/todo/page.tsx（需 'use client'，因使用状态与事件）

'use client';

import { useState } from 'react';

type Todo = { id: number; text: string; done: boolean };

export default function Todo() {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [input, setInput] = useState('');

  const addTodo = () => {
    if (!input.trim()) return;
    setTodos([...todos, { id: Date.now(), text: input.trim(), done: false }]); // 不可变
    setInput('');
  };

  const toggle = (id: number) => {
    setTodos(todos.map((t) => (t.id === id ? { ...t, done: !t.done } : t))); // 不可变
  };

  const remove = (id: number) => {
    setTodos(todos.filter((t) => t.id !== id));
  };

  return (
    <main style={{ padding: 40, maxWidth: 520, margin: '0 auto', fontFamily: 'sans-serif' }}>
      <h2>Todo 清单（客户端交互）</h2>
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && addTodo()}
          placeholder="输入新事项，回车添加"
          style={{ flex: 1, padding: 8 }}
        />
        <button onClick={addTodo}>添加</button>
      </div>

      {todos.length === 0 ? (
        <p style={{ color: '#888' }}>暂无事项</p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {todos.map((t) => (
            <li
              key={t.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: 8,
                borderBottom: '1px solid #eee',
                textDecoration: t.done ? 'line-through' : 'none',
                color: t.done ? '#999' : '#000',
              }}
            >
              <input type="checkbox" checked={t.done} onChange={() => toggle(t.id)} />
              <span style={{ flex: 1 }}>{t.text}</span>
              <button onClick={() => remove(t.id)}>删除</button>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}