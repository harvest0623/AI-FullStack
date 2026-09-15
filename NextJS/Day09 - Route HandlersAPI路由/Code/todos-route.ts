// Day09 - todos-route.ts  完整 Route Handler（GET/POST/DELETE）示例
// 落位：app/api/todos/route.ts

import { NextRequest, NextResponse } from 'next/server';

// 内存模拟数据库（真实项目替换为数据库/ORM）
let todos = [
  { id: 1, text: '学习 Next.js', done: false },
  { id: 2, text: '搭建 AI 对话应用', done: false },
];

// GET /api/todos —— 获取列表（支持 ?done=true 过滤）
export async function GET(req: NextRequest) {
  const doneStr = req.nextUrl.searchParams.get('done');
  let data = todos;

  if (doneStr !== null) {
    const done = doneStr === 'true';
    data = todos.filter((t) => t.done === done);
  }

  return NextResponse.json({ ok: true, data });
}

// POST /api/todos —— 新增
export async function POST(req: NextRequest) {
  const body = await req.json();

  // 简单输入校验
  if (!body.text || typeof body.text !== 'string') {
    return NextResponse.json({ error: 'text 字段必填且为字符串' }, { status: 400 });
  }

  const newTodo = { id: Date.now(), text: body.text, done: false };
  todos = [...todos, newTodo];
  return NextResponse.json({ ok: true, data: newTodo }, { status: 201 });
}

// DELETE /api/todos?id=1 —— 按 id 删除
export async function DELETE(req: NextRequest) {
  const id = Number(req.nextUrl.searchParams.get('id'));
  const existed = todos.some((t) => t.id === id);

  if (!existed) return NextResponse.json({ error: '未找到' }, { status: 404 });

  todos = todos.filter((t) => t.id !== id);
  return NextResponse.json({ ok: true });
}