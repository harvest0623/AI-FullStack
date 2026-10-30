# -*- coding: utf-8 -*-
"""
Day10 - 01 Agent 服务化（用标准库模拟 API 服务）

演示内容：
1. 同步接口：短任务直接返回结果
2. 异步接口：长任务提交后返回 task_id，后台执行
3. 任务队列与状态查询：queued -> running -> done/failed
4. 并发请求的处理（线程池）

不依赖 FastAPI/Flask，用标准库模拟服务的请求-响应循环，离线可运行。
"""

import time
import uuid
import threading
from queue import Queue
from dataclasses import dataclass, field


# ============================================================
# 第一部分：任务模型与状态
# ============================================================

class TaskStatus:
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class AsyncTask:
    task_id: str
    input: str
    status: str = TaskStatus.QUEUED
    result: str | None = None
    error: str | None = None
    progress: str = ""
    created_at: float = field(default_factory=time.time)
    finished_at: float | None = None


# ============================================================
# 第二部分：Agent 核心（模拟执行）
# ============================================================

def agent_core(task_input: str, progress_cb=None) -> str:
    """模拟 Agent 执行：3 个步骤"""
    steps = ["分析请求", "调用工具收集信息", "整合生成回答"]
    for i, s in enumerate(steps, 1):
        time.sleep(0.05)  # 模拟耗时
        if progress_cb:
            progress_cb(f"{i}/{len(steps)} {s}")
    return f"关于「{task_input}」的分析报告（含数据与结论）"


# ============================================================
# 第三部分：API 服务（模拟 FastAPI 行为）
# ============================================================

class AgentService:
    """
    模拟一个 Agent HTTP 服务：
    - POST /chat        同步接口：短任务
    - POST /tasks       异步接口：长任务
    - GET  /tasks/{id}  查询任务状态
    """

    def __init__(self, workers: int = 2):
        self.tasks: dict[str, AsyncTask] = {}
        self.queue: Queue = Queue()
        self.threads: list[threading.Thread] = []
        for _ in range(workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self.threads.append(t)

    # ---------- 同步接口 ----------
    def handle_chat(self, payload: dict) -> dict:
        """POST /chat：短任务，阻塞到完成再返回"""
        answer = agent_core(payload["message"])
        return {"code": 0, "data": {"answer": answer}}

    # ---------- 异步接口 ----------
    def submit_task(self, payload: dict) -> dict:
        """POST /tasks：长任务，立即返回 task_id"""
        task_id = f"T-{uuid.uuid4().hex[:8]}"
        self.tasks[task_id] = AsyncTask(task_id=task_id, input=payload["message"])
        self.queue.put(task_id)
        return {"code": 0, "data": {"task_id": task_id, "status": TaskStatus.QUEUED}}

    def query_task(self, task_id: str) -> dict:
        """GET /tasks/{id}"""
        task = self.tasks.get(task_id)
        if task is None:
            return {"code": 404, "error": "任务不存在"}
        return {
            "code": 0,
            "data": {
                "task_id": task.task_id,
                "status": task.status,
                "progress": task.progress,
                "result": task.result,
                "error": task.error,
            },
        }

    # ---------- 后台工作线程 ----------
    def _worker(self):
        while True:
            task_id = self.queue.get()
            task = self.tasks[task_id]
            task.status = TaskStatus.RUNNING
            try:
                task.result = agent_core(
                    task.input,
                    progress_cb=lambda p: setattr(task, "progress", p),
                )
                task.status = TaskStatus.DONE
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
            finally:
                task.finished_at = time.time()
                self.queue.task_done()


# ============================================================
# 第四部分：演示
# ============================================================

def main():
    svc = AgentService(workers=2)

    print("=" * 56)
    print("1. 同步接口：POST /chat（短任务，直接返回）")
    print("=" * 56)
    resp = svc.handle_chat({"message": "对比 A 和 B 两家供应商"})
    print(f"响应：{resp['data']['answer']}\n")

    print("=" * 56)
    print("2. 异步接口：POST /tasks（长任务，返回 task_id）")
    print("=" * 56)
    resp = svc.submit_task({"message": "生成年度采购分析报告"})
    task_id = resp["data"]["task_id"]
    print(f"响应：{{'task_id': '{task_id}', 'status': 'queued'}}\n")

    print("轮询 GET /tasks/{id}：")
    for _ in range(20):
        status = svc.query_task(task_id)["data"]
        print(f"  status={status['status']:<8} progress={status['progress'] or '-'}")
        if status["status"] in (TaskStatus.DONE, TaskStatus.FAILED):
            break
        time.sleep(0.03)

    final = svc.query_task(task_id)["data"]
    print(f"\n最终结果：{final['result']}")

    print()
    print("=" * 56)
    print("3. 并发请求：3 个任务同时提交，2 个 worker 消费")
    print("=" * 56)
    ids = [svc.submit_task({"message": f"任务 {i}"})["data"]["task_id"] for i in range(3)]
    print(f"提交了 3 个任务：{ids}")

    # 等待全部完成
    deadline = time.time() + 5
    while time.time() < deadline:
        statuses = [svc.query_task(i)["data"]["status"] for i in ids]
        if all(s == TaskStatus.DONE for s in statuses):
            break
        time.sleep(0.05)

    for i in ids:
        t = svc.query_task(i)["data"]
        dur = 0  # 演示场景时间短
        print(f"  {i}: {t['status']} | {t['result'][:30]}... | 耗时~{dur}")

    print("\n关键结论：")
    print("  - 同步接口适合 <10s 的短任务，超时会让用户挂死")
    print("  - 长任务必须异步：提交拿 task_id，轮询/回调拿结果")
    print("  - worker 数控制并发上限，防止 LLM 供应商被打爆")


if __name__ == "__main__":
    main()
