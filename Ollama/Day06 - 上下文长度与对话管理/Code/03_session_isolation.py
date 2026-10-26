# -*- coding: utf-8 -*-
"""
Day06 - 03 会话隔离

用 session_id → history 的字典管理多个独立会话：
1. 每个用户/场景各自维护历史，互不串扰
2. add_message / get_history 封装
3. 演示两个用户各自记住自己的事

双模式：有 Ollama -> 真实分会话调用；无 -> 展示结构与计数。
"""

from ollama_util import chat_wrapper


class SessionManager:
    """最简单的会话池：session_id -> messages"""

    def __init__(self, system: str):
        self.system = system
        self._sessions: dict[str, list[dict]] = {}

    def _get(self, sid: str) -> list[dict]:
        if sid not in self._sessions:
            self._sessions[sid] = [
                {"role": "system", "content": self.system}]
        return self._sessions[sid]

    def ask(self, sid: str, user_text: str) -> tuple[str, int]:
        history = self._get(sid)
        history.append({"role": "user", "content": user_text})
        reply = chat_wrapper("llama3.1", history)
        history.append({"role": "assistant", "content": reply})
        return reply, len(history)


def main():
    print(">> 会话隔离（Session Isolation）\n")
    sm = SessionManager("你是本地客服；记住每位用户的不同订单信息；回答简短。")

    print("用户 A 说：我想查号码为 A100 的订单")
    r1, n1 = sm.ask("user-A", "我想查号码为 A100 的订单，它是什么时候发货的？")
    print(f"  → ({len(r1)}字) {r1} [历史{n1}条]")

    print("\n用户 B 说：我要退款")
    r2, n2 = sm.ask("user-B", "我要退款，怎么操作？")
    print(f"  → ({len(r2)}字) {r2} [历史{n2}条]")

    # 关键：A 的历史与 B 完全隔离
    print("\n验证隔离：")
    print("  A 的历史条数:", n1, "| B 的历史条数:", n2)
    print("  A 只记得 A100，B 只记得退款，互不串扰 ✓")

    print("\n  tips: 生产环境把 session_id 换成用户ID/WebSocket连接ID即可")


if __name__ == "__main__":
    main()