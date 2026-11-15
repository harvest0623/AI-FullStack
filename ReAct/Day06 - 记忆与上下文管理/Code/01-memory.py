"""
Day06 练习一：记忆装箱与窗口截断
==================================
实现简单的 ConversationBufferMemory + token 预算截断。
演示历史增长时, 如何丢掉最旧的非 system 消息来约束上下文。

运行:
  python "Day06 - 记忆与上下文管理/Code/01-memory.py"
"""


def est_tokens(text: str) -> int:
    """粗略估算 token 数: 约 4 个字母/1 token。"""
    return len(text) // 4 + 1


class ConversationBufferMemory:
    def __init__(self, system: str = ""):
        self.messages = []
        if system:
            self.messages.append({"role": "system", "content": system})

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})

    def as_messages(self) -> list:
        return list(self.messages)

    def total_tokens(self) -> int:
        return sum(est_tokens(m["content"]) for m in self.messages)

    def trim(self, max_tokens: int) -> int:
        """超预算时, 从最旧的非 system 消息开始丢, 返回丢弃条数。"""
        dropped = 0
        while self.total_tokens() > max_tokens:
            # 找到第一个非 system 消息
            idx = next((i for i, m in enumerate(self.messages) if m["role"] != "system"), None)
            if idx is None:
                break
            self.messages.pop(idx)
            dropped += 1
        return dropped


def main() -> None:
    mem = ConversationBufferMemory(system="你是一个乐于助人的助手（系统提示, 永不删除）。")
    print("预算 = 120 tokens\n")

    # 模拟 8 轮很短对话, 让总长超过预算
    for i in range(8):
        mem.add("user", f"用户第 {i+1} 个问题：请介绍一下 product {i+1} 的价格、库存与评价信息")
        mem.add("assistant", f"助手第 {i+1} 回应：product {i+1} 价格 $10，库存充足，评价见上轮工具返回。")

    before = len(mem.messages)
    tok = mem.total_tokens()
    dropped = mem.trim(120)
    print(f"插入 {before-1} 条(不含system) 后, 预计 {tok} tokens")
    print(f"截断丢掉了 {dropped} 条历史, 现在 {mem.total_tokens()} tokens, 剩余 {len(mem.messages)} 条")
    print()
    print("剩余的 messages roles:", [m["role"] for m in mem.messages])
    print("最早保留的一条:", mem.messages[1]["content"][:30], "…")
    print("结论: 最新对话被保留, 最旧的被丢弃, 控制在预算内。")


if __name__ == "__main__":
    main()